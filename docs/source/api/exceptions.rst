Exceptions
==========

.. currentmodule:: pal.exceptions.core

PAL defines a hierarchy of exceptions for error handling.

Base Exception
--------------

PALError
~~~~~~~~

.. autoclass:: PALError
   :members:
   :show-inheritance:

Specific Exceptions
-------------------

PALValidationError
~~~~~~~~~~~~~~~~~~

.. autoclass:: PALValidationError
   :members:
   :show-inheritance:

PALLoadError
~~~~~~~~~~~~

.. autoclass:: PALLoadError
   :members:
   :show-inheritance:

PALCompilerError
~~~~~~~~~~~~~~~~

.. autoclass:: PALCompilerError
   :members:
   :show-inheritance:

PALExecutorError
~~~~~~~~~~~~~~~~

.. autoclass:: PALExecutorError
   :members:
   :show-inheritance:

PALResolverError
~~~~~~~~~~~~~~~~

.. autoclass:: PALResolverError
   :members:
   :show-inheritance:

PALMissingVariableError
~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: PALMissingVariableError
   :members:
   :show-inheritance:

PALMissingComponentError
~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: PALMissingComponentError
   :members:
   :show-inheritance:

PALCircularDependencyError
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: PALCircularDependencyError
   :members:
   :show-inheritance:

Exception Handling Examples
---------------------------

Basic error handling::

    from pal import PromptCompiler
    from pal.exceptions import PALError, PALMissingVariableError

    compiler = PromptCompiler()

    try:
        prompt = compiler.compile_from_file_sync("my_prompt.pal")
    except PALMissingVariableError as e:
        print(f"Missing variables: {e.context['missing_variables']}")
    except PALError as e:
        print(f"PAL error: {e}")

Detailed error information::

    from pal import Loader
    from pal.exceptions import PALValidationError

    loader = Loader()

    try:
        assembly = loader.load_prompt_assembly("invalid.pal")
    except PALValidationError as e:
        print(f"Validation failed: {e}")
        for error in e.context['validation_errors']:
            print(f"  - {error['loc']}: {error['msg']}")
