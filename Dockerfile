FROM openjdk:17-jdk-slim

WORKDIR /app

COPY build/libs/project.jar /app/project.jar

EXPOSE 8080

CMD ["java", "-jar", "project.jar"] 