from storages.utils import setting
from storages.backends.gcloud import GoogleCloudStorage


class GoogleCloudMediaStorage(GoogleCloudStorage):

    def __init__(self, *args, **kwargs):
        kwargs['location'] = setting('GS_MEDIA_LOCATION', 'media')
        super().__init__(*args, **kwargs)


class GoogleCloudStaticStorage(GoogleCloudStorage):

    def __init__(self, *args, **kwargs):
        kwargs['location'] = setting('GS_STATIC_LOCATION', 'static')
        super().__init__(*args, **kwargs)
