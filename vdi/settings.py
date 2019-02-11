
class Settings(dict):
    debug = True

    def __init__(self):
        cls = self.__class__
        super().__init__(**{
            k: v for k, v in cls.__dict__.items()
            if not k.startswith('__')
        })

settings = Settings()