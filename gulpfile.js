var gulp = require('gulp'),
    watch = require('gulp-watch'),
    runSequence = require('run-sequence'),
    rename = require('gulp-rename'),
    bower = require('gulp-bower'),
    prefixer = require('gulp-autoprefixer'),
    sass = require('gulp-sass'),
    del = require('del'),
    vulcanize = require('gulp-vulcanize'),
    sequence = require('gulp-watch-sequence'),
    sourcemaps = require('gulp-sourcemaps');

var config = {
    bowerDir: './bower_components/',
    elementsRoot: 'src/ralph/admin/static/elements/',
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
        'bower_components/foundation-datepicker/css/foundation-datepicker.css',
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
        './bower_components/webcomponentsjs/webcomponents-lite.js',
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
});


gulp.task('clean:elements', function () {
  return del([
    'src/ralph/admin/static/bower_components/',
  ]);
});
gulp.task('vulcanize', function () {
    return gulp.src(config.elementsRoot + 'elements.html')
        .pipe(vulcanize({
            abspath: '',
            excludes: [],
            stripExcludes: false,
            stripComments: true,
            inlineCss: true,
            inlineScripts: true
        }))
        .pipe(rename(config.elementsRoot + 'elements-min.html'))
        .pipe(gulp.dest('.'));
});
gulp.task('polymer-dev', function() {
    return gulp.src([
        "./bower_components/**/*"
    ], {base:"."})
        .pipe(gulp.dest("src/ralph/admin/static/"));
});


gulp.task('watch', function() {
    // run "gulp dev" before
    gulp.watch(config.srcRoot + 'scss/**/*.scss', ['scss']);
    gulp.watch([config.elementsRoot + '*.html', '!' + config.elementsRoot + '*-min.html'], ['vulcanize']);
});

gulp.task('dev', function(callback) {
    runSequence('bower', 'css', 'fonts', 'js', 'scss', 'polymer-dev', 'vulcanize', callback);
});

gulp.task('build', function(callback) {
    runSequence('dev', 'clean:elements', callback);
});

gulp.task('default', ['dev']);
