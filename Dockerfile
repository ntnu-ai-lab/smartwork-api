#
# Build stage
#
FROM maven:3.9.1-ibmjava-8 AS build
COPY mycbr-sdk/src /home/sdk/src
COPY mycbr-sdk/pom.xml /home/sdk
COPY mycbr-rest/src /home/rest/src
COPY mycbr-rest/pom.xml /home/rest
RUN mvn -f /home/sdk/pom.xml clean install
RUN mvn -f /home/rest/pom.xml clean install


#
# Package stage
#
FROM amazoncorretto:8u372
COPY --from=build /home/sdk/target/myCBR-3.3-SNAPSHOT.jar /home/sdk/mycbr_sdk.jar
COPY --from=build /home/rest/target/mycbr-rest-2.0.jar /home/rest/mycbr-rest-2.0.jar
EXPOSE 8080
# RUN ["touch","/home/MyCBR.prj"]
COPY mycbr-rest/pom.xml $PRJ_PATH ./

ENTRYPOINT java -DMYCBR.PROJECT.FILE=$PRJ_PATH -jar /home/rest/mycbr-rest-2.0.jar
