# Code Translation

A useful workflow with AI is to build initial versions of code in Python (slow) and then ask for translation to C++.

The AI has a reference working implementation. Often the AI only needs to implement a core speed critical routine. The ease of Python's ecosystem with mature wide ranging libraries makes this a rapid development route. The python code can then become a wrapper for the fast C++ code. This pattern is sometimes called 'hard and soft code'. The python provides the soft code that is easier to work with. The C++ provides the hard code that is more difficult to debug and change. 