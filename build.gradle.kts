import org.jetbrains.kotlin.gradle.tasks.KotlinCompile

plugins {
    kotlin("jvm") version "1.9.20"
    id("com.lagradost.cloudstream3.gradle") version "0.6.0"
}

group = "com.umar"
version = "1.0.0"

repositories {
    mavenCentral()
    maven("https://jitpack.io")
}

dependencies {
    // Cloudstream core dependency for API access
    compileOnly("com.lagradost:cloudstream3:latest-release")
    
    // Kotlin Standard Library
    implementation(kotlin("stdlib"))
}

tasks.withType<KotlinCompile> {
    kotlinOptions {
        jvmTarget = "1.8"
        freeCompilerArgs = freeCompilerArgs + "-Xjvm-default=all"
    }
}

cloudstream {
    // This blocks prevents build failures for the plugin 
    setCheck(false)
}
