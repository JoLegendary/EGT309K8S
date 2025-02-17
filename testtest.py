import requests
import regex
import inspect
__noinit_meta__ = type("",(type,),{"__call__": lambda cls, *vargs, **kwargs: cls.__new__(cls,*vargs,**kwargs)})
def paramify(context, vargs=[], kwargs={}):
	paramType = 0 if "/" in context else 1
	parameters = []
	for param in context:
		match(type(param).__name__):
			case "str":	param, paramDef = param, {}
			case "dict":	param, paramDef = [x for sub in [(k,{"default":v}) for k, v in param.items()] for x in sub]
			case wrongType: raise TypeError(f"Invalid type for 'context'. Only accepts 'str' and 'dict', got: {wrongType}")
		if param == "/":
			if paramType > 0: raise TypeError("Illegal syntax, '/' cannot be used here.")
			paramType = 1
		elif (paramName := regex.search(r"(?:^\*([^*]*)$)|()", param).group(1)) is not None:
			if paramType < 2: paramType = 3
			else: raise TypeError(f"Illegal syntax, {
				"Variable arguments cannot be used here" if paramName else "Positional-Only declaration cannot be used here"
			}.")
			if paramName:	parameters += [inspect.Parameter(paramName,2,**paramDef)]
		elif (paramName := regex.search(r"(?:^\*{2}([^*]*$))|()", param).group(1)) is not None:
			if paramName is None: raise TypeError("Illegal syntax, Variable keyword argument cannot be used without given a name")
			parameters += [inspect.Parameter(paramName,4,**paramDef)]
		else:
			parameters += [inspect.Parameter(param,paramType,**paramDef)]
	signature = inspect.Signature(parameters)
	return signature.bind(*vargs,**kwargs).arguments

class clientHeader(metaclass=__noinit_meta__):
    def __new__(cls,*vargs,**kwargs):
        if len(vargs) > 0 and type(vargs[0]) == cls:	return vargs[0]
        
        obj = super().__new__(cls)
        
        params = paramify([{"header":None}], vargs, kwargs)
        header = params["header"]
        
        if type(header) != requests.structures.CaseInsensitiveDict:
            raise ValueError("Only allow for headers!")
        obj.__header = header
        
        obj.__init__(*vargs, **kwargs)
        return obj
    def __getitem__(self, key):
        try:		wrapee = super().__getattribute__(f"_{__class__.__name__}__header")
        except:		raise TypeError("Not initialised yet!")
        if type(key) == str:
            return wrapee[key]
        raise TypeError("Only supports str")
    def __setitem__(self, key, val):
        try:		wrapee = super().__getattribute__(f"_{__class__.__name__}__header")
        except:		raise TypeError("Not initialised yet!")
        if type(key) == str:
            return wrapee.update({key: val})
        raise TypeError("Only supports str")
    def __getattribute__(self, key):
        try:		wrapee = super().__getattribute__(f"_{__class__.__name__}__header")
        except:		return super().__getattribute__(key)
        return getattr(wrapee, key)
    def __setattr__(self, key, val):
        try:		wrapee = super().__getattribute__(f"_{__class__.__name__}__header")
        except:		return super().__setattr__(key, val)
        return setattr(wrapee, key, val)
    def __delattr__(self, key):
        try:		wrapee = super().__getattribute__(f"_{__class__.__name__}__header")
        except:		return super().__delattr__(key)
        return delattr(wrapee, key)
    def __repr__(self):
        return f"<\"{__class__.__name__}\" Wrapper-object of header>"
    def __str__(self):
        try:		wrapee = super().__getattribute__(f"_{__class__.__name__}__header")
        except:		raise TypeError("Not initialised yet!")
        return str(wrapee)
        
class Client(metaclass=__noinit_meta__):
	uri = None
	session = None
	responses = None
	defaults = {
		"alwaysReferPrevious": True
	}
		
	def __new__(cls,*vargs,**kwargs):
		if len(vargs) > 0 and type(vargs[0]) == cls:
			return vargs[0]
		obj = super().__new__(cls)
		obj.__init__(*vargs, **kwargs)
		return obj
	def __init__(self, uri=None, ref=None, send=False, method="GET", *, cookies=None):
		self.session = requests.Session()
		self.header = clientHeader(self.session.headers)
		self.alwaysReferPrev = __class__.defaults["alwaysReferPrevious"]
		if uri is not None:
			self.uri = uri
			#self.session.headers["User-Agent"] = "Mozilla/5"
			
			if ref: self.session.headers.update({"Referer":ref})
			
			if cookies is not None: self.session.update(cookies)
			
			if send: self(method=method)
	def __call__(self, *vargs, method="GET", **kwargs):
		if len(vargs) > 0: self.uri = vargs[0]
		_method = None
		match(method.upper()):
			case "GET": _method = "get"
			case "POST": _method = "post"
			case "UPDATE": _method = "update"
			case "PUT": _method = "put"
			case "DELETE": _method = "delete"
			case _: raise TypeError("Invalid method.")
		if self.responses is None: self.responses = []
		if self.alwaysReferPrev is True and "Referer" not in kwargs:
			if self.responses is not None and len(self.responses) > 0 and (lastUrl := self.responses[-1].url):
				self.session.headers["Referer"] = lastUrl
		elif "Referer" in kwargs:
			if type(kwargs["Referer"]) == str:
				self.session.headers["Referer"] = kwargs["Referer"]
			del kwargs["Referer"]
		self.responses += [getattr(self.session, _method)(self.uri, **kwargs)]
		return self.responses[-1]
	def keys(self):
		return self.response.json().keys()
	def __getitem__(self, key):
		return self.response.json()[key]
	@property
	def cookies(self):
		return self.session.cookies

        
def test_post(client):
    try:
        response = client("https://localhost:7687/getrecommendation", json=dict(vehiclemode=1,mode=1,topn=1), method="POST", verify=False)
        if response.status_code == 404: raise Exception
    except:
        response = client("http://localhost:7687/getrecommendation", json=dict(vehiclemode=1,mode=1,topn=1), method="POST")
    return response
    
client = Client()
