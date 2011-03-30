# -*- coding: utf-8 -*-

"""
Generic extension system.

Overview
========
  pyAutoExtension is a simple module designed to help you design modular applications by providing mechanisms to auto-detect no classes at the run-time.

The ExtensionClass concept
==========================
  An extension class is simply a metaclass that keeps track of its instances. You can create new classes of extensions by subclassing ExtensionClass.

  Usually, you should create an (abstact) base class to use as a basis for any new class (aka type or family) of extensions. Thus, each subclass of this base class will automatically have your custom ExtensionClass as metaclass.

Mini how-to
===========

  >>> class MyExtensionClass(ExtensionClass):
  ...   extensionPolicy = NameBasedBlackListExtensionPolicy("")      # Ignore all the classes whose name is an empty string
  ...
  >>> class MyExtension1(object):
  ...   __metaclass__ = MyExtensionClass
  ...   name = "MyExtension1"
  ...
  >>> class MyExtension2(object):
  ...   __metaclass__ = MyExtensionClass
  ...   name = "MyExtension2"
  ...
  >>> print(sorted([Extension.name for Extension in MyExtensionClass.getAvailableExtensions()]))
  ['MyExtension1', 'MyExtension2']

  >>> # Using an existing metaclass (e. g.: ABCMeta)
  >>> import abc
  >>> class ABCMetaExtensionClass(abc.ABCMeta, BaseExtensionClass):
  ...   def __new__(mcls, name, bases, namespace):
  ...     return mcls._new(name, bases, namespace, abc.ABCMeta)
  ...
  >>> class MyOtherExtensionClass(ABCMetaExtensionClass):
  ...   extensionPolicy = NameBasedBlackListExtensionPolicy("")
  ...
  >>> class MyOtherAbstractExtension(object):
  ...   __metaclass__ = MyOtherExtensionClass
  ...   name = ""
  ...   
  ...   @abc.abstractmethod
  ...   def foo(self): pass
  ...
  >>> class MyOtherExtension1(MyOtherAbstractExtension):
  ...   name = "MyOtherExtension1"
  ...   
  ...   def foo(self): print("Hello")
  ...
  >>> class MyOtherExtension2(MyOtherAbstractExtension):
  ...   name = "MyOtherExtension2"
  ...
  ...   def foo(self): print("World")
  ...
  >>> print(sorted([Extension.name for Extension in MyOtherExtensionClass.getAvailableExtensions()]))
  ['MyOtherExtension1', 'MyOtherExtension2']
  >>> m = MyOtherAbstractExtension()
  Traceback (most recent call last):
    ...
  TypeError: Can't instantiate abstract class MyOtherAbstractExtension with abstract methods foo
  >>> m1 = MyOtherExtension1()

License
=======
  Generic extension system.

  Copyright (C) 2009, 2011 Florian Léger

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program.  If not, see U{http://www.gnu.org/licenses/}.

"""

__author__ = "Florian Léger"
__license__ = "GPLv3"
__copyright__ = "2009, 2011 Florian Léger"
__url__ = "https://github.com/fleger/pyAutoExtension"
__version__ = "1.1.1"

from glob import iglob
import os.path
import re
import operator

# Exception classes

class ExtensionError(Exception):
  """
  Base class for exceptions in this module.
  """
  pass


class ExtensionNameError(ExtensionError):
  """
  Exception raised when there is no extension name.
  """
  pass


class ExtensionNameAlreadyExistsError(ExtensionError):
  """
  Exception raised when an extension with the same name already exists.
  """
  pass


# Policies

class AbstractExtensionPolicy(object):
  """
  Abstract class for the extension policies.

  An extension policy allows an ExtensionClass to avoid registering some of its instances based on some criteria.

  You may define your own extension policies by subclassing this class and redefining the __call__ method.

  You may compose several ExtensionPolicy instances together using the operators | (or), & (and), ^ (xor), and ~ (not).
  """

  def __call__(self, name, bases, namespace):
    """
    Test if new class will be registered in its ExtensionClass.

    @param name:        Name of the new class.
    @type name:         str
    @param bases:       Base classes of the new class.
    @type bases:        tuple
    @param namespace:   The namespace of the new class.
    @type namespace:    dict

    @return: true if the class must be registered, false otherwise.
    @rtype: boolean

    @attention: name is the name given to the class during its definition, not the name of the extension. The name of the extension can be access though by using namespace["name"].
    """
    pass

  def __and__(self, other):
    if isinstance(other, AbstractExtensionPolicy):
      return ComposedExtensionPolicy(self, other, operator.and_)
    else:
      return NotImplemented

  def __or__(self, other):
    if isinstance(other, AbstractExtensionPolicy):
      return ComposedExtensionPolicy(self, other, operator.or_)
    else:
      return NotImplemented

  def __xor__(self, other):
    if isinstance(other, AbstractExtensionPolicy):
      return ComposedExtensionPolicy(self, other, operator.xor_)
    else:
      return NotImplemented

  def __invert__(self):
    return InvertedExtensionPolicy(self)


class ComposedExtensionPolicy(AbstractExtensionPolicy):
  """
  Composition of two extension policies by a logical operator.
  """
  def __init__(self, operand1, operand2, binaryOperator):
    """
    Creates a new ComposedExtensionPolicy instance.

    @param operand1:    First extension policy.
    @type operand1:     AbstractExtensionPolicy
    @param operand2:    Second extension policy.
    @type operand2:     AbstractExtensionPolicy
    @param binaryOperator:  Logical operator.
    @type binaryOperator:   function
    """
    self.operand1 = operand1
    self.operand2 = operand2
    self.binaryOperator = binaryOperator

  def __call__(self, name, bases, namespace):
    return self.binaryOperator(self.operand1(name, bases, namespace), self.operand2(name, bases, namespace))


class InvertedExtensionPolicy(AbstractExtensionPolicy):
  """
  Invert the result of an extension policy.
  """
  def __init__(self, originalPolicy):
    """
    Creates a new InvertedExtensionPolicy instance.

    @param originalPolicy:      The extension policy to invert.
    @type originalPolicy:       AbstractExtensionPolicy
    """
    self.originalPolicy = originalPolicy

  def __call__(self, name, bases, namespace):
    return not self.originalPolicy(name, bases, namespace)


class NameBasedWhiteListExtensionPolicy(AbstractExtensionPolicy):
  """
  Name-based white list extension policy.

  Allows the registration of a new extension if it's name is in a white list.
  """

  def __init__(self, *args):
    """
    Creates a new NameBasedWhiteListExtensionPolicy instance.

    @param args:      White list of allowed extension names.
    @type args:       str
    """
    self.__whiteList = set(args)

  @property
  def whiteList(self):
    """
    The white list.
    """
    return self.__whiteList

  def __call__(self, name, bases, namespace):
    return namespace["name"] in self.whiteList


class NameBasedREExtensionPolicy(AbstractExtensionPolicy):
  """
  Name based extension policy using a regular expression.

  Allows the registration of a new extension if it's name match a given regular expression pattern.
  """
  def __init__(self, pattern):
    self.pattern = pattern

  def __call__(self, name, bases, namespace):
    return True if re.match(self.pattern, namespace["name"]) else False


class NameBasedBlackListExtensionPolicy(AbstractExtensionPolicy):
  """
  Name-based black list extension policy.

  Allows the registration of a new extension if it's name is not in a black list.
  """
  def __init__(self, *args):
    """
    Creates a new NameBasedBlackListExtensionPolicy instance.

    @param args:      Black list of forbidden extension names.
    @type args:       str
    """
    self.__blackList = set(args)

  @property
  def blackList(self):
    """
    The black list.
    """
    return self.__blackList

  def __call__(self, name, bases, namespace):
    return namespace["name"] not in self.blackList


DefaultExtensionPolicy = NameBasedBlackListExtensionPolicy
"""
The default extension policy used when a new extension class is created.
"""

class _MetaExtensionClass(type):
  """
  Metaclass for the extension classes.

  For internal use.
  """
  
  def __new__(mcls, name, bases, namespace):
    if "extensionPolicy" not in namespace:
      namespace["extensionPolicy"] = DefaultExtensionPolicy()
    return type.__new__(mcls, name, bases, namespace)

  def __init__(self, name, bases, namespace):
    type.__init__(self, name, bases, namespace)
    self.__availableExtensions = {}

  @property
  def _availableExtensions(self):
    """
    Declared extensions.
    """
    return self.__availableExtensions


class BaseExtensionClass(object):
    """
    Base class for the extension metaclasses.

    Should not be used directly.
    """

    __metaclass__ = _MetaExtensionClass

    @classmethod
    def _new(mcls, name, bases, namespace, supermcls):
      """
      Creates a new extension class.
      """
      if "name" in namespace:
        if mcls.extensionPolicy(name, bases, namespace):
          if namespace["name"] not in mcls._availableExtensions:
            extension = supermcls.__new__(mcls, name, bases, namespace)
            mcls._availableExtensions[namespace["name"]] = extension
            return extension
          else:
            raise ExtensionNameAlreadyExistsError, "An extension named %s already exists at %s." %(namespace["name"], mcls._availableExtensions[namespace["name"]])
        else:
          return supermcls.__new__(mcls, name, bases, namespace)
      else:
        raise ExtensionNameError, "%s has no name." %name

    @classmethod
    def getAvailableExtensions(cls):
      """
      Get the available extension classes.

      @rtype:     tuple
      @return:    A tuple containing all the declared extension classes.
      """
      return tuple(cls._availableExtensions.values())


class ExtensionClass(type, BaseExtensionClass):
  """
  Metaclass for the extensions.

  Allows to keep tracks of each declared extension.

  @note: All the classes that have an extension class as metaclass must have a class attribute called name. This is the name of the extension. It's value must be unique within the same class of extensions.
  """

  def __new__(mcls, name, bases, namespace):
    return mcls._new(name, bases, namespace, type)


DEFAULT_EXTENSION_PATTERN = "[!_]*.py"
"""
Default extension module file name fnmatch pattern.
"""

def findExtensions(path, pattern=DEFAULT_EXTENSION_PATTERN):
  """
  Find all the extension modules in a given path.

  @note:  File extensions are stripped from the result.

  @param path:    The search path.
  @type path:     str
  @param pattern: fnmatch search pattern.
  @type pattern:  str

  @return:    An iterable containing all the module names.
  @rtype:     iterable
  """
  return (os.path.basename(s).rsplit(".", 1)[0] for s in iglob(os.path.join(path, pattern)))

if __name__ == "__main__":
  # Regression tests
  import doctest
  doctest.testmod()