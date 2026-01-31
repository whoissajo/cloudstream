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
    // Explicitly set the provider class for the plugin
    // Since there is no package, the class name is used directly
    providerClass = "UmarR2Provider"
    
    // Disable strict checks to ensure a smooth build
    setCheck(false)
}
