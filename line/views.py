import json
import logging
import os
import re
import requests
import traceback
import uuid
from datetime import (
    date, datetime, timedelta,
)

from linebot import (
    LineBotApi, WebhookParser,
)
from linebot.exceptions import (
    InvalidSignatureError, LineBotApiError,
)
from linebot.models import (
    FollowEvent, PostbackEvent, MessageEvent,
    TextMessage, ImageSendMessage, TextSendMessage, TemplateSendMessage,
    ButtonsTemplate, ConfirmTemplate, CarouselTemplate, CarouselColumn, ImageCarouselTemplate, ImageCarouselColumn,
    PostbackTemplateAction, DatetimePickerTemplateAction,
)

from django.conf import settings
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.db.models import (
    Count, Q,
)
from django.http import (
    HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseServerError,
)
from django.views.decorators.csrf import csrf_exempt

from accounts.models import User
from main.models import (
    Item, Reservation, Size, Type,
)


# Create your views here.

POSTAGE = 0

THANKS_FOR_FOLLOWING = '友達追加ありがとうございます！\n' \
                     + 'enyfarは、スーツケースを格安でレンタルすることができるサービスです\n' \
                     + 'お支払い以外の手続きを、すべてこのLINEトークルームで完結させることができます\n\n' \
                     + '下のボタンから、したい操作を選んでください'

THANKS_FOR_USING     = 'いつもご利用ありがとうございます！\n' \
                     + 'enyfarは、スーツケースを格安でレンタルすることができるサービスです\n' \
                     + 'お支払い以外の手続きを、すべてこのLINEトークルームで完結させることができます\n\n' \
                     + '下のボタンから、したい操作を選んでください'

SELECT_START_DATE    = 'レンタル開始日を選択してください'

SELECT_RETURN_DATE   = '返却日を選択してください'

INPUT_ZIP_CODE       = '郵便番号を入力してください\n' \
                     + '（半角数字7桁・ハイフンなし）\n\n' \
                     + '（例）1230001'

INPUT_ADDRESS        = '住所を入力してください\n\n' \
                     + '(例)東京都港区三田1-2-34 エニーカーサ101'

INPUT_NAME           = 'お名前（宛名）を入力してください\n' \
                     + '（姓と名の間にスペースを入れてください）\n\n' \
                     + '(例)山田 太郎'

INPUT_PHONE_NUMBER   = '電話番号を入力してください\n' \
                     + '（半角数字・ハイフンなし）\n\n' \
                     + '（例）09012345678'

ABOUT_PAYMENT        = 'お支払い方法と期限については、レンタル日前までにご連絡いたしますので、ご対応をお願い致します'



@csrf_exempt
def callback(request):

    # send error if request.method is not 'POST'
    if not request.method == 'POST':
        return HttpResponseBadRequest('<h1>Bad Request</h1><p>Your browser sent a request that this server could not understand.</p>')


    # create line object and get response
    line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
    parser = WebhookParser(settings.LINE_CHANNEL_SECRET)
    logger = logging.getLogger(__name__)

    body = request.body.decode('utf-8')
    signature = request.META['HTTP_X_LINE_SIGNATURE']

    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        return HttpResponseForbidden()
    except LineBotApiError:
        return HttpResponseBadRequest()


    # handle each event
    for event in events:
        line_id = event.source.user_id
        user, created = User.objects.get_or_create(line_id=line_id)
        if created:
            user.is_line_only = True
            user.save()
        reservations = Reservation.objects.filter(user=user).order_by('-created_at')
        reservation = Reservation.objects.filter(user=user).order_by('-created_at').first()

        url = "https://api.line.me/v2/bot/user/%s/richmenu/%s" % (line_id, settings.LINE_RICH_MENU_ID)
        headers = {"Authorization": "Bearer {%s}" % settings.LINE_CHANNEL_ACCESS_TOKEN}
        requests.post(url, headers=headers, verify=True).json()


        ###########
        ## utils ##
        ##########

        def item_date_checker():
            text = '条件に一致する商品はこちらになります\n' \
            + '詳細を見たい商品の「詳細を見る」タップしてください'
            items = Item.objects.filter(size=reservation.size, type=reservation.type).annotate(Count('reservation')).order_by('-reservation__count')

            for item in items:
                for r in item.reservation_set.all():
                    if r.uuid != reservation.uuid \
                    and not (r.return_date + timedelta(days=1) < reservation.start_date or reservation.return_date < r.start_date - timedelta(days=1)):
                        items = items.exclude(uuid=str(r.item.uuid))

            if not len(items):
                text = '条件に一致する商品が見つからなかったため、条件の類似した商品を表示しています\n' \
                + '詳細を見たい商品の「詳細を見る」タップしてください'
                items = Item.objects.filter(Q(size=reservation.size) or Q(type=reservation.type))

                for item in items:
                    for r in item.reservation_set.all():
                        if r.uuid != reservation.uuid \
                        and not (r.return_date + timedelta(days=1) < reservation.start_date or reservation.return_date < r.start_date - timedelta(days=1)):
                            items = items.exclude(uuid=str(r.item.uuid))

            return items, text

        def fee_calculator(item, days=None):
            intercept = item.fee_intercept
            coefs = item.item_fee_coef_set.order_by('starting_point')
            fee = intercept

            if not days:
                delta = reservation.return_date - reservation.start_date
                days = delta.days + 1

            for coef in coefs:
                fee_coef = coef.fee_coef
                starting_point = coef.starting_point
                end_point = coef.end_point

                if end_point:
                    if days <= end_point:
                        fee += fee_coef * (days - starting_point)
                        return round(fee, -1)
                    elif end_point < days:
                        fee += fee_coef * (end_point - starting_point)
                else:
                    fee += fee_coef * (days - starting_point)
                    return round(fee, -1)

            return fee


        ##############
        ## prompter ##
        ##############

        def text_message(arg):
            reply = line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(arg)
            )
            return reply

        def date_prompter(text1, text2, data, arg, min, max):
            reply = line_bot_api.reply_message(
                event.reply_token,
                [
                    TextSendMessage(text1),
                    TemplateSendMessage(
                        alt_text='日にちを選択してください',
                        template=ButtonsTemplate(
                            title='選択',
                            text=text2,
                            actions=[
                                DatetimePickerTemplateAction(
                                    label='選択',
                                    data=data,
                                    mode='date',
                                    initial=arg,
                                    min=min,
                                    max=max
                                )
                            ]
                        )
                    )
                ]
            )
            return reply

        def start_date_prompter(arg=None):
            arg = date.today() + timedelta(days=1)
            arg = arg.strftime('%Y-%m-%d')
            min = date.today() + timedelta(days=1)
            min = min.strftime('%Y-%m-%d')
            max = date.today() + timedelta(days=365)
            max = max.strftime('%Y-%m-%d')

            if datetime.strptime(arg, '%Y-%m-%d') < datetime.strptime(min, '%Y-%m-%d'):
                min = arg
            reply = date_prompter(SELECT_START_DATE, SELECT_START_DATE, 'start_date', arg, min, max)
            return reply

        def return_date_prompter(arg=None, check=False):
            start_date_check = '開始日は {}年{}月{}日 ですね\n\n次は、'.format(
                reservation.start_date.year,
                reservation.start_date.month,
                reservation.start_date.day
            )
            text1 = text2 = SELECT_RETURN_DATE
            if check:
                text1 = start_date_check + text1

            min = reservation.start_date + timedelta(days=2)
            min = min.strftime('%Y-%m-%d')
            max = date.today() + timedelta(days=367)
            max = max.strftime('%Y-%m-%d')

            if arg:
                if reservation.return_date <= reservation.start_date - 1:
                    arg = min
                else:
                    pass
            else:
                arg = min

            reply = date_prompter(text1, text2, 'return_date', arg, min, max)
            return reply

        def size_prompter(check=False):
            delta = reservation.return_date - reservation.start_date
            days = delta.days + 1

            sizes = Size.objects.order_by('min_days')
            actions = [
                PostbackTemplateAction(label='{} ({}～{}L)'.format(size.name, size.min_capacity, size.max_capacity), data=str(size.uuid))
                if size.max_capacity else
                PostbackTemplateAction(label='{} ({}L～)'.format(size.name, size.min_capacity), data=str(size.uuid))
                for size in sizes
            ]

            for size in sizes:
                min = size.min_days
                max = size.max_days
                if max:
                    if min <= days < max:
                        recommendation = size
                elif not max:
                    if min <= days:
                        recommendation = size

            return_date_check = '返却日は {}年{}月{}日 ですね\n\n次は、'.format(
                reservation.return_date.year,
                reservation.return_date.month,
                reservation.return_date.day
            )
            size_prompt = 'サイズを選択してください\n'
            size_recommend = '{}日間のレンタルなら、\n\n {}サイズ '.format(days, recommendation.name)

            if recommendation.max_capacity:
                size_recommend += '({}～{}L)\n\nがおすすめです'.format(recommendation.min_capacity, recommendation.max_capacity)
            else:
                size_recomend += '({}L～)\n\nがおすすめです'.format(recommendation.min_capacity)

            size_prompt += size_recommend
            text = size_prompt
            if check:
                text = return_date_check + text

            reply = line_bot_api.reply_message(
                event.reply_token,
                [
                    TextSendMessage(text),
                    TemplateSendMessage(
                        alt_text=size_prompt,
                        template=ButtonsTemplate(
                            title='サイズを選択',
                            text=size_recommend,
                            actions=actions
                        )
                    )
                ]
            )
            return reply

        def type_prompter(check=False):
            size_check = '{}サイズですね\n\n次は、'.format(reservation.size)
            text = 'スーツケースの鍵・明け口のタイプを選択してください'
            if check:
                text = size_check + text

            types = Type.objects.all()

            columns = [
                CarouselColumn(
                    thumbnail_image_url=type.image.url,
                    title=type.name,
                    text=type.description,
                    actions=[
                        PostbackTemplateAction(
                            label='このタイプにする',
                            data=str(type.uuid)
                        )
                    ]
                )
                for type, _ in zip(types, range(0, 10))
            ]

            reply = line_bot_api.reply_message(
                event.reply_token,
                [
                    TextSendMessage(text),
                    TemplateSendMessage(
                        alt_text='スーツケースの鍵・明け口のタイプを選択してください',
                        template=CarouselTemplate(
                            columns=columns
                        )
                    )
                ]
            )
            return reply

        def item_selection_prompter(start=0):
            items, text1 = item_date_checker()
            end = len(items) if len(items) <= start + 9 else start + 9

            columns = [
                CarouselColumn(
                    thumbnail_image_url = items[i].item_image_set.order_by('order')[0].image.url,
                    title = items[i].name,
                    text = '価格：￥{}～\n'.format(round(items[i].fee_intercept + items[i].item_fee_coef_set.order_by('starting_point')[0].fee_coef * 2, -1)) \
                         + 'ブランド：{}\n'.format(items[i].bland),
                    actions = [
                        PostbackTemplateAction(
                             label='詳細を見る',
                             data=str(items[i].uuid)
                         )
                    ]
                )
                for i in range(start, end)
            ]

            if len(items) > start + 9:
                columns.append(
                    CarouselColumn(
                        thumbnail_image_url=static('line/img/plus.png'),
                        title='もっと見る',
                        text='更に商品を見たい場合、下の「もっと見る」をタップしてください',
                        actions=[
                            PostbackTemplateAction(
                                 label='もっと見る',
                                 data=str(start + 9)
                             )
                        ]
                    )
                )

            messages = [
                TemplateSendMessage(
                    alt_text='商品を選択してください',
                    template=CarouselTemplate(
                        image_aspect_ratio='square',
                        columns=columns
                    )
                )
            ]
            if start == 0:
                messages.insert(0, TextSendMessage(text1))

            reply = line_bot_api.reply_message(
                event.reply_token,
                messages
            )
            return reply

        def item_decision_prompter(arg):
            item = Item.objects.get(uuid=arg)

            text = '商品の詳細です\n' \
                 + 'こちらの商品でよろしいですか？\n\n' \
                 + '【商品詳細】\n\n' \
                 + '商品名：\n{}\n\n'.format(item.name) \
                 + 'ブランド：\n{}\n\n'.format(item.bland) \
                 + '容量：\n{}L ({})\n\n'.format(item.capacity, item.size) \
                 + 'タイプ：\n{}\n\n'.format(item.type) \
                 + 'カラー：\n{}\n\n'.format(item.color) \
                 + '料金（送料を含む）：\n￥{}'.format(fee_calculator(item))
            item_images = item.item_image_set.order_by('order')

            columns = [
                ImageCarouselColumn(
                    image_url=item_image.image.url,
                    action=PostbackTemplateAction(
                         label='画像{}'.format(str(item_image.order)),
                         data='_'
                     )
                )
                for item_image, _ in zip(item_images, range(0, 10))
            ]

            reply = line_bot_api.reply_message(
                event.reply_token,
                [
                    TemplateSendMessage(
                        alt_text='商品画像',
                        template=ImageCarouselTemplate(
                            columns=columns
                        )
                    ),
                    TextSendMessage(text),
                    TemplateSendMessage(
                        alt_text='こちらの商品でよろしければ「はい」、別の商品を探す場合は「いいえ」を選択してください',
                        template=ConfirmTemplate(
                            text='こちらの商品でよろしいですか？',
                            actions=[
                                PostbackTemplateAction(
                                    label='はい',
                                    data=str(item.uuid)
                                ),
                                PostbackTemplateAction(
                                    label='いいえ',
                                    data='not_choose'
                                ),
                            ]
                        )
                    )
                ]
            )
            return reply

        def date_adding_prompter():
            delta = reservation.return_date - reservation.start_date
            days = delta.days + 1

            item = reservation.item
            add_one_days =  fee_calculator(item, days+1) - fee_calculator(item, days)
            add_two_days =  fee_calculator(item, days+2) - fee_calculator(item, days+1)
            extra = int(round(fee_calculator(item, 2) / 2, -1))

            text = '商品を保存しました\n\n' \
                 + '現在{}日間で予約されていますが、余裕を持って準備・返却するために、前後に日数を追加することをオススメしています\n'.format(days) \
                 + '（事前にご報告なく延長された場合は、{}円/1日をいただいています）\n\n'.format(extra) \
                 + '日数をプラスしますか？'

            reply = line_bot_api.reply_message(
                event.reply_token,
                [
                    TextSendMessage(text),
                    TemplateSendMessage(
                        alt_text='現在{}日間で予約されていますが、余裕をもって準備・返却するために、たった{}円でレンタル日数を1日増やすことができます\n' \
                                .format(days, add_one_days, add_two_days) \
                                +'日数をプラスしますか？',
                        template=ButtonsTemplate(
                            title='日にちを追加',
                            text='日にちを追加しますか？',
                            actions=[
                                PostbackTemplateAction(label='前に1日 (+{}円)'.format(add_one_days), data='add_before'),
                                PostbackTemplateAction(label='後ろに1日 (+{}円)'.format(add_one_days), data='add_after'),
                                PostbackTemplateAction(label='前後に1日ずつ (+{}円)'.format(add_one_days + add_two_days), data='add_both'),
                                PostbackTemplateAction(label='追加しない', data='not_add')
                            ]
                        )
                    )
                ]
            )
            return reply

        def use_default_address_prompter(check=False):
            text = '次のお届け先が以前使用されました\n' \
                 + 'このお届け先を使用しますか？\n\n' \
                 + '【お届け先情報】\n' \
                 + '〒{}-{}\n'.format(user.zip_code1, user.zip_code2) \
                 + '{}\n'.format(user.address) \
                 + 'お名前：{} {}\n'.format(user.last_name, user.first_name)

            if check:
                text = 'レンタル日数を追加しました\n\n' + text


            reply = line_bot_api.reply_message(
                event.reply_token,
                [
                    TextSendMessage(text),
                    TemplateSendMessage(
                        alt_text='このお届け先を使用しますか？',
                        template=ConfirmTemplate(
                            text='保存されているお届け先を使用しますか？',
                            actions=[
                                PostbackTemplateAction(
                                    label='はい',
                                    data='use_default'
                                ),
                                PostbackTemplateAction(
                                    label='いいえ',
                                    data='not_use_default'
                                ),
                            ]
                        )
                    )
                ]
            )
            return reply

        def check_prompter(check=False):
            text = '項目の入力が完了しました\n' \
                 + '予約内容は以下の通りです\n\n\n' \
                 + '【予約内容】\n\n' \
                 + '開始日：\n{}年{}月{}日\n\n'.format(reservation.start_date.year, reservation.start_date.month, reservation.start_date.day) \
                 + '返却日：\n{}年{}月{}日\n\n'.format(reservation.return_date.year, reservation.return_date.month, reservation.return_date.day) \
                 + '住所：\n〒{}-{} {}\n\n'.format(reservation.zip_code1, reservation.zip_code2, reservation.address) \
                 + 'お名前：\n{} {}\n\n\n'.format(reservation.last_name, reservation.first_name) \
                 + '【料金】\n\n' \
                 + '小計：￥{}\n'.format(reservation.item_fee) \
                 + '送料：￥{}\n\n'.format(reservation.postage) \
                 + 'ご請求額：￥{}\n\n\n'.format(reservation.total_fee) \
                 + '【商品詳細】\n\n' \
                 + '商品名：\n{}\n\n'.format(reservation.item.name) \
                 + 'ブランド：\n{}\n\n'.format(reservation.item.bland) \
                 + '容量：\n{}L ({})\n\n'.format(reservation.item.capacity, reservation.item.size) \
                 + 'タイプ：\n{}\n\n'.format(reservation.item.type) \
                 + 'カラー：\n{}\n\n\n'.format(reservation.item.color) \
                 + 'この内容で予約を確定する場合は「確定」、予約内容を修正する場合は「修正」、予約を中止する場合は「中止」を押してください'

            if check:
                text = 'レンタル日数を追加しました\n\n' + text

            reply = line_bot_api.reply_message(
                event.reply_token,
                [
                    TextSendMessage(text),
                    TemplateSendMessage(
                        alt_text='予約を確定する場合は「確定」、予約内容を修正する場合は「修正」、予約を中止する場合は「中止」を押してください',
                        template=ButtonsTemplate(
                            title='確認',
                            text='予約内容を確認し、操作を選んでください',
                            actions=[
                                PostbackTemplateAction(
                                    label='確定',
                                    data='confirm'
                                ),
                                PostbackTemplateAction(
                                    label='修正',
                                    data='modify'
                                ),
                                PostbackTemplateAction(
                                    label='中止',
                                    data='delete'
                                ),
                            ]
                        )
                    )
                ]
            )
            return reply

        def registration_prompter():
            text = '予約が確定しました\n' \
                 + '今回のお届け先を次回以降も利用できるように保存しますか？\n\n' \
                 + '【お届け先】\n' \
                 + '〒{}-{}\n'.format(reservation.zip_code1, reservation.zip_code2) \
                 + '{}\n'.format(reservation.address) \
                 + 'お名前：{} {}'.format(reservation.last_name, reservation.first_name)

            reply = line_bot_api.reply_message(
                event.reply_token,
                [
                    TextSendMessage(text),
                    TemplateSendMessage(
                        alt_text='お届け先を保存する場合は「はい」、保存しない場合は「いいえ」を選択してください？',
                        template=ConfirmTemplate(
                            text='次回以降、このお届け先を利用できるように保存しますか？',
                            actions=[
                                PostbackTemplateAction(
                                    label='はい',
                                    data='register'
                                ),
                                PostbackTemplateAction(
                                    label='いいえ',
                                    data='not_register'
                                ),
                            ]
                        )
                    )
                ]
            )
            return reply

        def modification_prompter():
            text = 'どの項目を修正しますか？\n\n' \
                 + '・レンタルする日にちを変更したい場合は「レンタル期間」\n' \
                 + '・住所・お名前・電話番号を変更したい場合は「お届け先情報」\n' \
                 + '・商品を変更したい場合は「商品」\n\n' \
                 + 'をタップしてください'

            reply = line_bot_api.reply_message(
                event.reply_token,
                [
                    TextSendMessage(text),
                    TemplateSendMessage(
                        alt_text='修正したい項目をタップしてください',
                        template=ButtonsTemplate(
                            title='修正',
                            text='修正したい項目をタップしてください',
                            actions=[
                                PostbackTemplateAction(
                                    label='レンタル期間',
                                    data='modify_rental_period'
                                ),
                                PostbackTemplateAction(
                                    label='商品',
                                    data='modify_item'
                                ),
                                PostbackTemplateAction(
                                    label='お届け先情報',
                                    data='modify_destination'
                                ),
                            ]
                        )
                    )
                ]
            )
            return reply

        def item_modification_prompter():
            text = 'アイテムを探す方法を選択してください'

            reply = line_bot_api.reply_message(
                event.reply_token,
                [
                    TextSendMessage(text),
                    TemplateSendMessage(
                        alt_text='アイテムを探す方法を選択してください',
                        template=ButtonsTemplate(
                            title='アイテムを探す',
                            text='方法を選択してください',
                            actions=[
                                PostbackTemplateAction(
                                    label='類似商品を表示する',
                                    data='list_item'
                                ),
                                PostbackTemplateAction(
                                    label='条件を変更する',
                                    data='modify_condition'
                                )
                            ]
                        )
                    )
                ]
            )
            return reply

        def item_condition_modification_prompter():
            reservation.item = None
            reservation.save()
            text = 'どの項目を修正しますか？\n\n' \
                 + '修正したい項目をタップしてください'

            reply = line_bot_api.reply_message(
                event.reply_token,
                [
                    TextSendMessage(text),
                    TemplateSendMessage(
                        alt_text='修正したい項目をタップしてください',
                        template=ButtonsTemplate(
                            title='修正',
                            text='修正したい項目をタップしてください',
                            actions=[
                                PostbackTemplateAction(
                                    label='サイズ：{}'.format(reservation.size),
                                    data='modify_size'
                                ),
                                PostbackTemplateAction(
                                    label='タイプ：{}'.format(reservation.type),
                                    data='modify_type'
                                )
                            ]
                        )
                    )
                ]
            )
            return reply

        def destination_modification_prompter():
            text = 'どの項目を修正しますか？\n\n' \
                 + '修正したい項目をタップしてください'

            reply = line_bot_api.reply_message(
                event.reply_token,
                [
                    TextSendMessage(text),
                    TemplateSendMessage(
                        alt_text='修正したい項目をタップしてください',
                        template=ButtonsTemplate(
                            title='修正',
                            text='修正したい項目をタップしてください',
                            actions=[
                                PostbackTemplateAction(
                                    label='郵便番号・住所',
                                    data='modify_address'
                                ),
                                PostbackTemplateAction(
                                    label='お名前',
                                    data='modify_name'
                                )
                            ]
                        )
                    )
                ]
            )
            return reply

        def deletion_prompter():
            text = '予約を中止しますか？\n' \
                 + '入力した内容は完全に削除されます\n\n' \
                 + '※この操作は取り消せません\n' \

            reply = line_bot_api.reply_message(
                event.reply_token,
                [
                    TextSendMessage(text),
                    TemplateSendMessage(
                        alt_text='予約を中止する場合は「はい」、中止しない場合は「いいえ」を選択してください',
                        template=ConfirmTemplate(
                            text='予約を中止しますか？この操作は取り消せません',
                            actions=[
                                PostbackTemplateAction(
                                    label='はい',
                                    data='delete'
                                ),
                                PostbackTemplateAction(
                                    label='いいえ',
                                    data='not_delete'
                                ),
                            ]
                        )
                    )
                ]
            )
            return reply

        def reconfirmation_prompter():
            text = '現在、予約済みの商品は{}個あります\n'.format(reservations.count()) \
                 + '詳細を見たい予約をタップしてください'

            columns = [
                CarouselColumn(
                    thumbnail_image_url = r.item.item_image_set.order_by('order')[0].image.url,
                    title = '{}/{}/{} ～ {}/{}/{}'.format(
                        r.start_date.year,
                        r.start_date.month,
                        r.start_date.day,
                        r.return_date.year,
                        r.return_date.month,
                        r.return_date.day
                    ),
                    text = '〒{}-{} {}\n'.format(
                        r.zip_code1,
                        r.zip_code2,
                        r.address
                    ),
                    actions=[
                        PostbackTemplateAction(
                             label='詳細を見る',
                             data=str(r.uuid)
                         )
                    ]
                )
                for r, _ in zip(reservations, range(0, 10))
            ]

            reply = line_bot_api.reply_message(
                event.reply_token,
                [
                    TextSendMessage(text),
                    TemplateSendMessage(
                        alt_text='詳細を見たい予約をタップしてください',
                        template=CarouselTemplate(
                            image_aspect_ratio='square',
                            columns=columns
                        )
                    )
                ]
            )
            return reply

        def remodification_prompter():
            obj = reservations.get(uuid=event.postback.data)
            text1 = '予約内容は以下の通りです\n\n\n' \
                  + '【予約内容】\n\n' \
                  + '開始日：\n{}年{}月{}日\n\n'.format(obj.start_date.year, obj.start_date.month, obj.start_date.day) \
                  + '返却日：\n{}年{}月{}日\n\n'.format(obj.return_date.year, obj.return_date.month, obj.return_date.day) \
                  + 'お届け先住所：\n〒{}-{} {}\n\n'.format(obj.zip_code1, obj.zip_code2, obj.address) \
                  + 'お名前：\n{} {}\n\n\n'.format(obj.last_name, obj.first_name) \
                  + '【料金】\n\n' \
                  + '小計：￥{}\n'.format(obj.item_fee) \
                  + '送料：￥{}\n\n'.format(obj.postage) \
                  + '合計料金：￥{}\n\n\n'.format(obj.total_fee) \
                  + '【商品詳細】\n\n' \
                  + '商品名：\n{}\n\n'.format(obj.item.name) \
                  + 'ブランド：\n{}\n\n'.format(obj.item.bland) \
                  + '容量：\n{}L ({})\n\n'.format(obj.item.capacity, obj.item.size) \
                  + 'タイプ：\n{}\n\n'.format(obj.item.type) \
                  + 'カラー：\n{}'.format(obj.item.color)
            text2 = '予約を変更、または取り消したい場合には、以下のメールアドレスまでご連絡ください\n\n' \
                  + 'メール：{}'.format(settings.EMAIL_HOST_USER)

            reply = line_bot_api.reply_message(
                event.reply_token,
                [
                    TextSendMessage(text1),
                    TextSendMessage(text2)
                ]
            )
            return reply


        ##############
        ## reciever ##
        ##############

        def thanks(text):
            reply = line_bot_api.reply_message(
                event.reply_token,
                [
                    TextSendMessage(text),
                    TemplateSendMessage(
                        alt_text='「予約する」または「予約の確認」を選択してください',
                        template=ButtonsTemplate(
                            title='操作',
                            text='下のボタンを押すと次へ進みます',
                            actions=[
                                PostbackTemplateAction(
                                    label='予約する',
                                    data='reservation'
                                ),
                                PostbackTemplateAction(
                                    label='予約の確認',
                                    data='reconfirmation'
                                ),
                            ]
                        )
                    )
                ]
            )
            return reply

        def thanks_for_following():
            thanks(THANKS_FOR_FOLLOWING)

        def thanks_for_using():
            if isinstance(event, MessageEvent) and isinstance(event.message, TextMessage):
                if event.message.text in ['予約', '予約する', '予約したい', '新規予約', '新規予約する', '新規予約したい', 'よやく', 'しんきよやく']:
                    reservation = Reservation(user=user, status=1)
                    reservation.save()
                    start_date_prompter()
                elif event.message.text in ['予約履歴', '履歴']:
                    if reservations.count():
                        reconfirmation_prompter()
                    else:
                        text_message('予約されている商品はありません')
                else:
                    thanks(THANKS_FOR_USING)

            elif isinstance(event, PostbackEvent):
                uuid_ = None
                try:
                    uuid_ = uuid.UUID(event.postback.data)
                except ValueError:
                    pass

                if event.postback.data == 'reservation':
                    reservation = Reservation(user=user, status=1)
                    reservation.save()
                    start_date_prompter()
                elif event.postback.data == 'reconfirmation':
                    if reservations.count():
                        reconfirmation_prompter()
                    else:
                        text_message('予約されている商品はありません')
                elif uuid_ in reservations.values_list('uuid', flat=True):
                    reservation_selected = reservations.get(uuid=event.postback.data)
                    remodification_prompter()

        def rich_menu_reciever():
            if event.postback.data == 'quit':
                if reservation:
                    if reservation.status:
                        reservation.delete()
                        text_message('予約を中止しました')
                    else:
                        text_message('現在行っている操作はありません\nリッチメニューから操作を選んでください')
                else:
                    text_message('現在行っている操作はありません\nリッチメニューから操作を選んでください')

        def start_date_reciever(next_status, func, check=False, **kwargs):
            if isinstance(event, PostbackEvent):
                if event.postback.data == 'start_date':
                    reservation.start_date = datetime.strptime(event.postback.params['date'], '%Y-%m-%d').date()
                    reservation.status = next_status
                    reservation.save()
                    if check:
                        try:
                            func(check=check)
                        except TypeError:
                            func(arg=kwargs['arg'], check=check)
                    else:
                        if 'arg' in kwargs:
                            func(arg=kwargs['arg'])
                        else:
                            func()

        def return_date_reciever(next_status, func, check=False, **kwargs):
            if isinstance(event, PostbackEvent):
                if event.postback.data == 'return_date':
                    reservation.return_date = datetime.strptime(event.postback.params['date'], '%Y-%m-%d').date()
                    reservation.status = next_status
                    reservation.save()
                    if reservation.item:
                        reservation.item_fee = fee_calculator(item=reservation.item)
                        reservation.postage = POSTAGE
                        reservation.total_fee = reservation.item_fee + reservation.postage
                        reservation.save()
                    if check:
                        try:
                            func(check=check)
                        except TypeError:
                            func(arg=kwargs['arg'], check=check)
                    else:
                        if 'arg' in kwargs:
                            func(arg=kwargs['arg'])
                        else:
                            func()


        def size_reciever(next_status, func, check=False, **kwargs):
            if isinstance(event, PostbackEvent):
                uuids = [str(u) for u in Size.objects.all().values_list('uuid', flat=True)]
                if event.postback.data in uuids:
                    reservation.size = Size.objects.get(uuid=event.postback.data)
                    reservation.status = next_status
                    reservation.save()
                    if check:
                        try:
                            func(check=check)
                        except TypeError:
                            func(arg=kwargs['arg'], check=check)
                    else:
                        if 'arg' in kwargs:
                            func(arg=kwargs['arg'])
                        else:
                            func()

            if isinstance(event, MessageEvent) and isinstance(event.message, TextMessage):
                names = Size.objects.all().values_list('name', flat=True)
                if event.message.text in names:
                    reservation.size = Size.objects.get(name=event.message.text)
                    reservation.status = next_status
                    reservation.save()
                    if 'arg' in kwargs:
                        func(arg=kwargs['arg'])
                    else:
                        func()

        def type_reciever(next_status, func, **kwargs):
            if isinstance(event, PostbackEvent):
                uuids = [str(u) for u in Type.objects.all().values_list('uuid', flat=True)]
                if event.postback.data in uuids:
                    reservation.type = Type.objects.get(uuid=event.postback.data)
                    reservation.status = next_status
                    reservation.save()
                    if 'arg' in kwargs:
                        func(arg=kwargs['arg'])
                    else:
                        func()

            if isinstance(event, MessageEvent) and isinstance(event.message, TextMessage):
                names = Type.objects.all().values_list('name', flat=True)
                if event.message.text in names:
                    reservation.type = Type.objects.get(name=event.message.text)
                    reservation.status = next_status
                    reservation.save()
                    if 'arg' in kwargs:
                        func(arg=kwargs['arg'])
                    else:
                        func()

        def item_selection_reciever(next_status, func, **kwargs):
            if isinstance(event, PostbackEvent):
                uuids = [str(u) for u in Item.objects.all().values_list('uuid', flat=True)]
                if event.postback.data in uuids:
                    reservation.status = next_status
                    reservation.save()
                    if 'arg' in kwargs:
                        func(arg=kwargs['arg'])
                    else:
                        func()
                elif event.postback.data.isdecimal():
                    num = int(event.postback.data)
                    item_selection_prompter(start=num)

        def item_decision_reciever(next_status, func, prompt_default=False, **kwargs):
            if isinstance(event, PostbackEvent):
                uuids = [str(u) for u in Item.objects.all().values_list('uuid', flat=True)]
                if event.postback.data in uuids:
                    reservation.item = Item.objects.get(uuid=event.postback.data)
                    reservation.size = reservation.item.size
                    reservation.type = reservation.item.type
                    reservation.item_fee = fee_calculator(item=reservation.item)
                    reservation.postage = POSTAGE
                    reservation.total_fee = reservation.item_fee + reservation.postage
                    if prompt_default and user.zip_code1 and user.zip_code2 and user.address and user.first_name and user.last_name:
                        reservation.status = 11
                        reservation.save()
                        use_default_address_prompter()
                    else:
                        reservation.status = next_status[0]
                        reservation.save()
                        if 'arg' in kwargs:
                            if kwargs['arg'][0]:
                                func[0](arg=kwargs['arg'][0])
                            else:
                                func[0]()
                        else:
                            func[0]()
                elif event.postback.data == 'not_choose':
                    reservation.status = next_status[1]
                    reservation.save()
                    if 'arg' in kwargs:
                        if kwargs['arg'][1]:
                            func[1](arg=kwargs['arg'][1])
                        else:
                            func[1]()
                    else:
                        func[1]()

            if isinstance(event, MessageEvent) and isinstance(event.message, TextMessage):
                names = Item.objects.all().values_list('name', flat=True)
                if event.message.text in names or event.postback.data == 'はい':
                    reservation.item = Item.objects.get(name=event.message.text)
                    reservation.size = reservation.item.size
                    reservation.type = reservation.item.type
                    reservation.item_fee = fee_calculator(reservation.item)
                    reservation.postage = POSTAGE
                    reservation.total_fee = reservation.item_fee + reservation.postage
                    if prompt_default and user.zip_code1 and user.zip_code2 and user.address and user.first_name and user.last_name:
                        reservation.status = 11
                        reservation.save()
                        use_default_address_prompter()
                    else:
                        reservation.status = next_status[0]
                        reservation.save()
                        if 'arg' in kwargs:
                            if kwargs['arg'][0]:
                                func[0](arg=kwargs['arg'][0])
                            else:
                                func[0]()
                        else:
                            func[0]()
                elif event.message.text == 'いいえ':
                    reservation.status = next_status2
                    reservation.save()
                    if 'arg' in kwargs:
                        if kwargs['arg'][1]:
                            func[1](arg=kwargs['arg'][1])
                        else:
                            func[1]()
                    else:
                        func[1]()

        def date_adding_reciever(next_status, func, check=False, prompt_default=False, **kwargs):
            if isinstance(event, PostbackEvent):
                if event.postback.data == 'add_both':
                    reservation.start_date = reservation.start_date - timedelta(days=1)
                    reservation.return_date = reservation.return_date + timedelta(days=1)
                elif event.postback.data == 'add_before':
                    reservation.start_date = reservation.start_date - timedelta(days=1)
                elif event.postback.data == 'add_after':
                    reservation.return_date = reservation.return_date + timedelta(days=1)
                elif event.postback.data == 'not_add':
                    pass
                reservation.item_fee = fee_calculator(item=reservation.item)
                reservation.total_fee = reservation.item_fee + reservation.postage

                if prompt_default and user.zip_code1 and user.zip_code2 and user.address and user.first_name and user.last_name:
                    reservation.status = 11
                    reservation.save()
                    if check:
                        use_default_address_prompter(check=True)
                    else:
                        use_default_address_prompter()
                else:
                    reservation.status = next_status
                    reservation.save()
                    if check:
                        try:
                            func(check=check)
                        except TypeError:
                            func(arg=kwargs['arg'], check=check)
                    else:
                        if 'arg' in kwargs:
                            func(arg=kwargs['arg'])
                        else:
                            func()

        def zip_code_reciever(next_status, func, **kwargs):
            if isinstance(event, MessageEvent) and isinstance(event.message, TextMessage):
                text = event.message.text
                if len(text) == 7 and text.isdecimal() and text.encode('utf-8').isalnum():
                    reservation.zip_code1 = text[:3]
                    reservation.zip_code2 = text[3:]
                    reservation.status = next_status
                    reservation.save()
                    user.save()
                    if 'arg' in kwargs:
                        func(arg=kwargs['arg'])
                    else:
                        func()
                elif len(text) == 7 and text.isdecimal() and not text.encode('utf-8').isalnum():
                    text_message('半角で入力してください')
                elif len(text) == 8 and text.find('-') == 3:
                    text_message('ハイフンなしで入力してください')
                else:
                    text_message('半角数字7桁・ハイフンなしで入力してください')

        def address_reciever(next_status, func, **kwargs):
            if isinstance(event, MessageEvent) and isinstance(event.message, TextMessage):
                reservation.address = event.message.text
                reservation.status = next_status
                reservation.save()
                user.save()
                if 'arg' in kwargs:
                    func(arg=kwargs['arg'])
                else:
                    func()

        def name_reciever(next_status, func, **kwargs):
            if isinstance(event, MessageEvent) and isinstance(event.message, TextMessage):
                text = event.message.text
                if text.find(' ') or text.find('　'):
                    name_list = [x for x in re.split(" |　", text) if x]
                    reservation.last_name = name_list[0]
                    reservation.first_name = ' \s'.join(name_list[1:])
                    reservation.status = next_status
                    reservation.save()
                    user.save()
                    if 'arg' in kwargs:
                        func(arg=kwargs['arg'])
                    else:
                        func()
                else:
                    text_message('姓と名の間にスペースを入れてください')

        def use_default_address_reciever(**kwargs):
            if isinstance(event, PostbackEvent):
                if event.postback.data == 'use_default':
                    reservation.zip_code1 = user.zip_code1
                    reservation.zip_code2 = user.zip_code2
                    reservation.address = user.address
                    reservation.first_name = user.first_name
                    reservation.last_name = user.last_name
                    reservation.status = 91
                    reservation.save()
                    check_prompter()
                elif event.postback.data == 'not_use_default':
                    reservation.status = 12
                    reservation.save()
                    text_message(INPUT_ZIP_CODE)

        def registration_reciever():
            if isinstance(event, PostbackEvent):
                if event.postback.data == 'register':
                    user.zip_code1 = reservation.zip_code1
                    user.zip_code2 = reservation.zip_code2
                    user.address = reservation.address
                    user.first_name = reservation.first_name
                    user.last_name = reservation.last_name
                    user.save()
                    reservation.status = 0
                    reservation.save()
                    text_message('お届け先を保存しました\n\n' + ABOUT_PAYMENT)
                elif event.postback.data == 'not_register':
                    if not user.first_name or user.last_name:
                        user.first_name = reservation.first_name
                        user.last_name = reservation.last_name
                        user.save()
                    reservation.status = 0
                    reservation.save()
                    text_message('予約が全て完了しました\n' + ABOUT_PAYMENT)

        def postback_reciever(data, next_status, func, **kwargs):
            if isinstance(event, PostbackEvent):
                for i in range(0, len(data)):
                    if event.postback.data == data[i]:
                        reservation.status = next_status[i]
                        reservation.save()
                        if 'arg' in kwargs:
                            if kwargs['arg'][i]:
                                func[i](arg=kwargs['arg'][i])
                            else:
                                func[i]()
                        else:
                            func[i]()

        def deletion_reciever():
            if isinstance(event, PostbackEvent):
                if event.postback.data == 'delete':
                    reservation.delete()
                    text_message('予約を中止しました')
                elif event.postback.data == 'not_delete':
                    reservation.status = 91
                    reservation.save()
                    check_prompter()


        ###################
        ## error handler ##
        ###################

        def error_handler():
            if reservation:
                if reservation.status:
                    reservation.delete()
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    '操作中にエラーが発生しました\n' + \
                    'お手数ですが操作を最初からやり直してください\n\n' + \
                    '何度もエラーが発生する場合は、以下のメールアドレスまでご連絡ください\n\n{}'.format(settings.EMAIL_HOST_USER)
                )
            )


        ##################
        ## main process ##
        ##################

        try:
            if isinstance(event, FollowEvent):
                thanks_for_following()
            elif isinstance(event, PostbackEvent):
                rich_menu_reciever()
            elif not reservation:
                thanks_for_using()

            # send default message
            if reservation.status == 0:
                thanks_for_using()

            # get item information
            elif reservation.status == 1:
                start_date_reciever(next_status=2, func=return_date_prompter, check=True)
            elif reservation.status == 2:
                return_date_reciever(next_status=3, func=size_prompter, check=True)
            elif reservation.status == 3:
                size_reciever(next_status=4, func=type_prompter, check=True)
            elif reservation.status == 4:
                type_reciever(next_status=5, func=item_selection_prompter)
            elif reservation.status == 5:
                item_selection_reciever(next_status=6, func=item_decision_prompter, arg=event.postback.data)
            elif reservation.status == 6:
                item_decision_reciever(next_status=(7, 21), func=(date_adding_prompter, item_modification_prompter))
            elif reservation.status == 7:
                date_adding_reciever(next_status=8, func=text_message, arg='レンタル日数を追加しました\n\n' + INPUT_ZIP_CODE, prompt_default=True)
            elif reservation.status == 8:
                zip_code_reciever(next_status=9, func=text_message, arg=INPUT_ADDRESS)
            elif reservation.status == 9:
                address_reciever(next_status=10, func=text_message, arg=INPUT_NAME)
            elif reservation.status == 10:
                name_reciever(next_status=91, func=check_prompter)

            # get user information (default data)
            elif reservation.status == 11:
                use_default_address_reciever()
            elif reservation.status == 12:
                zip_code_reciever(next_status=9, func=text_message, arg=INPUT_ADDRESS)

            # get user information (new data)
            elif reservation.status == 21:
                postback_reciever(
                    next_status=(22, 25),
                    func=(item_condition_modification_prompter, item_selection_prompter),
                    data=('modify_condition', 'list_item')
                )
            elif reservation.status == 22:
                postback_reciever(
                    next_status=(23, 24),
                    func=(size_prompter, type_prompter),
                    data=('modify_size', 'modify_type')
                )
            elif reservation.status == 23:
                size_reciever(next_status=25, func=item_selection_prompter)
            elif reservation.status == 24:
                type_reciever(next_status=25, func=item_selection_prompter)
            elif reservation.status == 25:
                item_selection_reciever(next_status=26, func=item_decision_prompter, arg=event.postback.data)
            elif reservation.status == 26:
                item_decision_reciever(next_status=(7, 21), func=(date_adding_prompter, item_modification_prompter))

            # modify reservation
            elif reservation.status == 31:
                start_date_reciever(next_status=32, func=return_date_prompter, arg=str(reservation.return_date), check=True)
            elif reservation.status == 32:
                return_date_reciever(next_status=43, func=size_prompter, check=True)
            elif reservation.status == 33:
                size_reciever(next_status=35, func=item_selection_prompter)
            elif reservation.status == 34:
                type_reciever(next_status=35, func=item_selection_prompter)
            elif reservation.status == 35:
                item_selection_reciever(next_status=36, func=item_decision_prompter, arg=event.postback.data)
            elif reservation.status == 36:
                item_decision_reciever(next_status=(91, 94), func=(check_prompter, item_modification_prompter))
            elif reservation.status == 37:
                zip_code_reciever(next_status=38, func=text_message, arg=INPUT_ADDRESS)
            elif reservation.status == 38:
                address_reciever(next_status=91, func=check_prompter)
            elif reservation.status == 39:
                name_reciever(next_status=91, func=check_prompter)

            # modify item information (with date information)
            elif reservation.status == 43:
                size_reciever(next_status=44, func=type_prompter, check=True)
            elif reservation.status == 44:
                type_reciever(next_status=45, func=item_selection_prompter)
            elif reservation.status == 45:
                item_selection_reciever(next_status=46, func=item_decision_prompter, arg=event.postback.data)
            elif reservation.status == 46:
                item_decision_reciever(next_status=(47, 94), func=(date_adding_prompter, item_modification_prompter))
            elif reservation.status == 47:
                date_adding_reciever(next_status=91, func=check_prompter, check=True)

            # confirm reservation
            elif reservation.status == 91:
                postback_reciever(
                    next_status=(92, 93, 99),
                    func=(registration_prompter, modification_prompter, deletion_prompter),
                    data=('confirm', 'modify', 'delete')
                )
            elif reservation.status == 92:
                registration_reciever()
            elif reservation.status == 93:
                postback_reciever(
                    next_status=(31, 94, 96),
                    func=(start_date_prompter, item_modification_prompter, destination_modification_prompter),
                    arg=(str(reservation.start_date), None, None),
                    data=('modify_rental_period', 'modify_item', 'modify_destination')
                )
            elif reservation.status == 94:
                postback_reciever(
                    next_status=(95, 35),
                    func=(item_condition_modification_prompter, item_selection_prompter),
                    data=('modify_condition', 'list_item')
                )
            elif reservation.status == 95:
                postback_reciever(
                    next_status=(33, 34),
                    func=(size_prompter, type_prompter),
                    data=('modify_size', 'modify_type')
                )
            elif reservation.status == 96:
                postback_reciever(
                    next_status=(37, 39),
                    func=(text_message, text_message),
                    arg=(INPUT_ZIP_CODE, INPUT_NAME),
                    data=('modify_address', 'modify_name')
                )

            # delete reservation
            elif reservation.status == 99:
                deletion_reciever()

        except:
            # error handling
            error_handler()
            traceback.print_exc()
            return HttpResponseServerError()

    return HttpResponse()
