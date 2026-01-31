#!/bin/sh
##############################################################################
##
##  Gradle start up script for UN*X
##
##############################################################################
APP_HOME=$(pwd)
APP_NAME="Gradle"
CLASSPATH=$APP_HOME/gradle/wrapper/gradle-wrapper.jar
exec java -classpath "$CLASSPATH" org.gradle.wrapper.GradleWrapperMain "$@"
