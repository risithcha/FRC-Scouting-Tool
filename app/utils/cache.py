from flask_caching import Cache
from app.utils.cache_tracker import update_cache_info, record_cache_hit
import functools

# Initialize cache
cache = Cache()

def init_cache(app):
    cache_config = {
        'CACHE_TYPE': 'simple',
        'CACHE_DEFAULT_TIMEOUT': 300
    }
    app.config.from_mapping(cache_config)
    cache.init_app(app)
    
    # Initialize tracking
    with app.app_context():
        try:
            update_cache_info('general', active=False, items=0)
            update_cache_info('stats', active=False, items=0)
            update_cache_info('tba', active=False, items=0)
        except Exception as e:
            print(f"Warning: Could not initialize cache tracking: {e}")
    
    return cache

# Create tracked versions of cache
def tracked_memoize(timeout=300, cache_type='general'):
    # A tracks cache usage
    def decorator(func):
        cached_func = cache.memoize(timeout=timeout)(func)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Check if result is coming from cache
            result = cached_func(*args, **kwargs)
            # Record the record for tracking
            try:
                record_cache_hit(cache_type)
            except Exception:
                # Ignore tracking errors (Heh heh heh)
                pass
            return result
        
        # Store the original uncached function to access later
        wrapper.uncached = func
        wrapper.cache_type = cache_type
        return wrapper
    
    return decorator