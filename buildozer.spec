[app]
title = FitTrack
package.name = fittrack
package.domain = ua.kpi.likanov
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,otf,mp4,db,sql,svg
version = 1.0
requirements = python3,kivy==2.3.0,kivymd==1.2.0,pillow,qrcode,bcrypt
orientation = portrait
fullscreen = 0
android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, CAMERA
android.api = 33
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.private_storage = True
icon.filename = assets/icons/app_icon.png
presplash.filename = assets/icons/splash.png
android.presplash_color = #0A0E27

[buildozer]
log_level = 2
warn_on_root = 1
