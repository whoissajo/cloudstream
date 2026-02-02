import com.android.build.gradle.BaseExtension
import com.lagradost.cloudstream3.gradle.CloudstreamExtension
import org.jetbrains.kotlin.gradle.tasks.KotlinCompile

buildscript {
    repositories {
        google()
        mavenCentral()
        maven("https://jitpack.io")
    }

    dependencies {
        classpath("com.android.tools.build:gradle:8.7.3")
        classpath("com.github.recloudstream:gradle:-SNAPSHOT")
        classpath("org.jetbrains.kotlin:kotlin-gradle-plugin:1.9.24")
    }
}

allprojects {
    repositories {
        google()
        mavenCentral()
        maven("https://jitpack.io")
    }
}

fun Project.cloudstream(configuration: CloudstreamExtension.() -> Unit) = extensions.getByName<CloudstreamExtension>("cloudstream").configuration()
fun Project.android(configuration: BaseExtension.() -> Unit) = extensions.getByName<BaseExtension>("android").configuration()

subprojects {
    apply(plugin = "com.android.library")
    apply(plugin = "kotlin-android")
    apply(plugin = "com.lagradost.cloudstream3.gradle")

    cloudstream {
        setRepo(System.getenv("GITHUB_REPOSITORY") ?: "whoissajo/cloudstream")
        authors = listOf("Umar")
    }

    android {
        namespace = "com.umar.r2.${project.name.lowercase()}"
        compileSdkVersion(35)

        defaultConfig {
            minSdk = 26 // Updated to match CloudX
            targetSdk = 35
        }

        compileOptions {
            sourceCompatibility = JavaVersion.VERSION_1_8
            targetCompatibility = JavaVersion.VERSION_1_8
        }

        tasks.withType<KotlinCompile> {
            kotlinOptions {
                jvmTarget = "1.8"
                freeCompilerArgs = freeCompilerArgs + listOf(
                    "-Xno-call-assertions",
                    "-Xno-param-assertions",
                    "-Xno-receiver-assertions",
                    "-Xskip-metadata-version-check"
                )
            }
        }
    }

    dependencies {
        val cloudstream by configurations
        val implementation by configurations

        cloudstream("com.lagradost:cloudstream3:pre-release")

        implementation(kotlin("stdlib"))
        implementation("com.github.Blatzar:NiceHttp:0.4.13") // Matches CloudX
        implementation("org.jsoup:jsoup:1.19.1") // Matches CloudX
        implementation("com.fasterxml.jackson.module:jackson-module-kotlin:2.16.0") // Matches CloudX
        implementation("com.fasterxml.jackson.core:jackson-databind:2.16.0") // Matches CloudX
        implementation("com.google.code.gson:gson:2.11.0") // Added from CloudX
        implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.10.1") // Added from CloudX
        implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.8.0")
    }
}

task<Delete>("clean") {
    delete(rootProject.layout.buildDirectory)
}
