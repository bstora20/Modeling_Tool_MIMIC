#exceptions.py

class ModelingToolError(Exception):
    """Base Exception for all modeling tool errors"""
    pass

class ComponentError(ModelingToolError):
    """Error with component definition or execution"""
    pass

class TaskError(ModelingToolError):
    """Error with task definition or execution"""
    pass

class ParserError(ModelingToolError):
    """Error parsing a component file"""
    pass

class ValidationError(ModelingToolError):
    """Error validation component definition"""
    pass
