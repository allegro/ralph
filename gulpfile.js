var gulp = require('gulp');
    less = require('gulp-less'),
    watch = require('gulp-watch'),
    runSequence = require('run-sequence'),
    rename = require('gulp-rename'),
    bower = require('gulp-bower');

var config = {
     bowerDir: './bower_components',
     dstRoot: 'src/ralph/admin/static/'
}

gulp.task('bower', function() { 
    return bower()
         .pipe(gulp.dest(config.bowerDir)) 
});

gulp.task('css', function() { 
    return gulp.src('bower_components/normalize.css/normalize.css') 
        .pipe(gulp.dest(config.dstRoot + '/css')); 
});

gulp.task('fonts', function() { 
    return gulp.src('bower_components/fontawesome/fonts/*.*') 
        .pipe(gulp.dest(config.dstRoot + '/fonts')); 
});

gulp.task('vendors', function(){
    var vendorFiles = [
        './bower_components/fastclick/lib/fastclick.js',
        './bower_components/jquery.cookie/jquery.cookie.js',
        './bower_components/jquery/dist/jquery.js',
        './bower_components/modernizr/modernizr.js',
    ];
    gulp.src(vendorFiles)
        .pipe(gulp.dest(config.dstRoot + 'js/vendor'));
    gulp.src('./bower_components/jquery-placeholder/jquery.placeholder.js')
        .pipe(rename('placeholder.js'))
        .pipe(gulp.dest(config.dstRoot + 'js/vendor'));

    var angularFiles = [
        './bower_components/angular-breadcrumb/dist/angular-breadcrumb.min.js',
        './bower_components/angular-cookies/angular-cookies.min.js',
        './bower_components/angular/angular.min.js',
        './bower_components/angular-resource/angular-resource.min.js',
        './bower_components/angular-route/angular-route.min.js',
        './bower_components/angular-ui-router/release/angular-ui-router.min.js',
    ]
    gulp.src(angularFiles)
        .pipe(gulp.dest('src/ralph/dc_view/static/js/vendor'));
});

var lessDir = './src/ralph/dc_view/static/css/'
gulp.task('less', function() {
    var lessFilesButNoUnderscoreAtBeginning = '[!_]*.less';
    return gulp.src(lessDir + lessFilesButNoUnderscoreAtBeginning)
        .pipe(less())
        .on('error', console.error.bind(console))
        .pipe(gulp.dest(lessDir));
});

gulp.task('watch', function() {
    gulp.watch(lessDir + '*.less', ['less']);
});

gulp.task('dev', function(callback) {
	runSequence('bower', 'css', 'fonts', 'vendors', 'less', callback);
});

gulp.task('default', ['dev']);
