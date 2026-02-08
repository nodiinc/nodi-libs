import inspect

def get_variable_name(variable, target_object=None):
    """Get variable name as string from object or frame"""
    
    # If target object is given
    if target_object:

        # Search attributes from the target object
        for attribute_name in dir(target_object):

            # Get variable name from the target object
            if getattr(target_object, attribute_name, None) is variable:
                return attribute_name

    # If target object is not given
    else:

        # Search local variables from this frame
        frame = inspect.currentframe().f_back
        for variable_name, value in frame.f_locals.items():
            
            # Get variable name from this frame
            if value is variable:
                return variable_name
    
    # If nothing found
    return None

def get_location(self):
    frame = inspect.currentframe().f_back
    return self.__class__.__name__, inspect.getframeinfo(frame).function

if __name__ == '__main__':

    class MyClass:
        def __init__(self):
            self.core = object()  # 고유한 객체 생성
            self.meta = object()

            self.mdl = {}
            self.mdl[self.core] = None
            self.mdl[self.meta] = None

    # 실행 예시
    mc = MyClass()

    # 객체 속성에서 변수명 찾기
    for item in mc.mdl:
        key_name = get_variable_name(item, mc)  # 객체 속성에서 찾기
        print(key_name)  # core, meta

    # 전역 변수 찾기 예시
    some_var = 123
    print(get_variable_name(some_var))  # some_var