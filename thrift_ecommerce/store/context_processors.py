from .models import StoreSettings

def store_info(request):
    # This allows us to use {{ store.store_name }} in any HTML file
    return {
        'store': StoreSettings.load()
    }