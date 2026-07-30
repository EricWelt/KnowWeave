// ═══════════════════════════════════════════
// android/build.gradle.kts（根项目）
// ═══════════════════════════════════════════

// Flutter 的 plugin-loader 由 settings.gradle.kts 的 includeBuild 注入
// 这里【绝对不要】写 plugins { id("dev.flutter...") version "1.0.0" }

// ── Flutter 模板的 build 目录重定向 ──
val newBuildDir: Directory =
    rootProject.layout.buildDirectory
        .dir("../../build")
        .get()
rootProject.layout.buildDirectory.value(newBuildDir)

subprojects {
    val newSubprojectBuildDir: Directory = newBuildDir.dir(project.name)
    project.layout.buildDirectory.value(newSubprojectBuildDir)
}

subprojects {
    project.evaluationDependsOn(":app")
}

tasks.register<Delete>("clean") {
    delete(rootProject.layout.buildDirectory)
}