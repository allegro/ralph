var gulp = require('gulp'),
    watch = require('gulp-watch'),
    runSequence = require('run-sequence'),
    rename = require('gulp-rename'),
    bower = require('gulp-bower'),
    prefixer = require('gulp-autoprefixer'),
    sass = require('gulp-sass'),
    sourcemaps = require('gulp-sourcemaps'),
    qunit = require('gulp-qunit');

var config = {
    bowerDir: './bower_components/',
    srcRoot: 'src/ralph/static/src/',
    staticRoot: 'src/ralph/static/',
    vendorRoot: 'src/ralph/static/vendor/'
}

var sass_config = {
    outputStyle: 'compressed',
    includePaths: [
        config.bowerDir + 'foundation/scss',
        config.bowerDir + 'fontawesome/scss',
        config.bowerDir + 'chartist/dist/scss',
    ]
}

gulp.task('bower', function() { 
    return bower()
         .pipe(gulp.dest(config.bowerDir)) 
});

gulp.task('scss', function() {
    gulp.src(config.srcRoot + 'scss/*.scss')
        .pipe(sourcemaps.init())
        .pipe(sass(sass_config).on('error', sass.logError))
        .pipe(prefixer())
        .pipe(sourcemaps.write('.'))
        .pipe(gulp.dest(config.staticRoot + 'css/'))
});

gulp.task('css', function() { 
    var vendorFiles = [
        'bower_components/normalize.css/normalize.css',
        'bower_components/foundation-datepicker/stylesheets/foundation-datepicker.css',
        'bower_components/angular-loading-bar/build/loading-bar.min.css',
    ];
    return gulp.src(vendorFiles) 
        .pipe(gulp.dest(config.vendorRoot + 'css/')); 
});

gulp.task('fonts', function() { 
    return gulp.src('bower_components/fontawesome/fonts/*.*') 
        .pipe(gulp.dest(config.vendorRoot + 'fonts/')); 
});

gulp.task('js', function(){
    var vendorFiles = [
        './bower_components/fastclick/lib/fastclick.js',
        './bower_components/jquery.cookie/jquery.cookie.js',
        './bower_components/jquery/dist/jquery.js',
        './bower_components/modernizr/modernizr.js',
        './bower_components/foundation/js/foundation.min.js',
        './bower_components/foundation-datepicker/js/foundation-datepicker.js',
        './bower_components/angular-loading-bar/build/loading-bar.min.js',
        './bower_components/raven-js/dist/raven.min.js',
        './bower_components/chartist/dist/chartist.js',
    ];
    gulp.src(vendorFiles)
        .pipe(gulp.dest(config.vendorRoot + 'js/'));
    gulp.src('./bower_components/jquery-placeholder/jquery.placeholder.js')
        .pipe(rename('placeholder.js'))
        .pipe(gulp.dest(config.vendorRoot + 'js'));

    var angularFiles = [
        './bower_components/angular-breadcrumb/dist/angular-breadcrumb.min.js',
        './bower_components/angular-cookies/angular-cookies.min.js',
        './bower_components/angular/angular.min.js',
        './bower_components/angular-resource/angular-resource.min.js',
        './bower_components/angular-route/angular-route.min.js',
        './bower_components/angular-ui-router/release/angular-ui-router.min.js',
    ]
    gulp.src(angularFiles)
        .pipe(gulp.dest(config.vendorRoot + 'js'));


    gulp.src([
        "./bower_components/font-roboto/**/*",
        "./bower_components/iron-a11y-keys/**/*",
        "./bower_components/iron-a11y-keys-behavior/**/*",
        "./bower_components/iron-ajax/**/*",
        "./bower_components/iron-autogrow-textarea/**/*",
        "./bower_components/iron-behaviors/**/*",
        "./bower_components/iron-collapse/**/*",
        "./bower_components/iron-flex-layout/**/*",
        "./bower_components/iron-form/**/*",
        "./bower_components/iron-form-element-behavior/**/*",
        "./bower_components/iron-input/**/*",
        "./bower_components/iron-menu-behavior/**/*",
        "./bower_components/iron-meta/**/*",
        "./bower_components/iron-selector/**/*",
        "./bower_components/iron-validatable-behavior/**/*",
        "./bower_components/paper-input/**/*",
        "./bower_components/paper-item/**/*",
        "./bower_components/paper-menu/**/*",
        "./bower_components/paper-styles/**/*",
        "./bower_components/polymer/**/*",
        "./bower_components/promise-polyfill/**/*",
        "./bower_components/webcomponentsjs/**/*",
    ], {base:"."})
        .pipe(gulp.dest("src/ralph/admin/static/"));
});

gulp.task('test', function() {
    return gulp.src('./src/ralph/js_tests/*_runner.html').pipe(qunit());
});

gulp.task('watch', function() {
    gulp.watch(config.srcRoot + 'scss/**/*.scss', ['scss']);
});

gulp.task('dev', function(callback) {
    runSequence('bower', 'css', 'fonts', 'js', 'scss', callback);
});

gulp.task('default', ['dev']);
