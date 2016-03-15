class Common(object):
    DEBUG = False


class Prod(Common):
    pass


class Dev(Common):
    DEBUG = True
