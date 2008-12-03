# Process this file with autoconf to produce a configure script.
AC_PREREQ(2.57)
AC_INIT(libroutez)

AC_PROG_CC
AC_PROG_CXX
AC_PROG_CPP
AC_PROG_CXXCPP
AX_PYTHON
AX_BOOST_PYTHON

AC_LANG_CPLUSPLUS

if test x"$BOOST_PYTHON_LIB" = "x"; then
    AC_MSG_ERROR("boost python not found")
fi

AC_CONFIG_FILES(config.mk)

AC_OUTPUT
