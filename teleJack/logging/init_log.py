def init_log(init_func):
    def initialization(*args, **kwargs):
        print(f"Initialization {init_func.__module__}.{init_func.__qualname__}...")
        data = init_func(*args, **kwargs)
        print(f"{init_func.__module__}.{init_func.__qualname__} is done!")
        return data
    return initialization
