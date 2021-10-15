const webpack = require("webpack");
const path = require("path");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");

module.exports = {
    mode: "development",
    entry: "./src/ralph/static/src/entry.js",
    output: {
        filename: "bundle.js",
        path: path.resolve(__dirname, "dist"),
    },
    resolve: {
        alias: {
            foundation: path.join(
                __dirname,
                "node_modules",
                "foundation-sites",
                "scss"
            ),
            "font-awesome": path.join(
                __dirname,
                "node_modules",
                "font-awesome",
                "scss"
            ),
        },
    },
    plugins: [new MiniCssExtractPlugin()],
    module: {
        rules: [
            {
                test: /\.js$/,
                exclude: /node_modules/,
                loader: "babel-loader",
                options: {
                    presets: ["@babel/preset-env"],
                },
            },
            {
                test: /\.html$/,
                use: [
                    { loader: "babel-loader" },
                    { loader: "polymer-webpack-loader" },
                ],
            },
            {
                test: /\.(woff(2)?|ttf|eot|svg)(\?v=\d+\.\d+\.\d+)?$/,
                use: [
                    {
                        loader: "file-loader",
                        options: {
                            name: "[name].[ext]",
                            outputPath: "fonts/",
                        },
                    },
                ],
            },
            {
                test: /\.s[ac]ss$/,
                use: [
                    MiniCssExtractPlugin.loader,
                    "css-loader",
                    {
                        loader: "sass-loader",
                        options: {
                            sassOptions: {
                                includePaths: [
                                    path.join(
                                        __dirname,
                                        "node_modules",
                                        "foundation-sites",
                                        "scss"
                                    ),
                                    path.join(
                                        __dirname,
                                        "node_modules",
                                        "fontawesome",
                                        "scss"
                                    ),
                                    path.join(
                                        __dirname,
                                        "node_modules",
                                        "chartist",
                                        "dist",
                                        "scss"
                                    ),
                                ],
                            },
                        },
                    },
                ],
            },
        ],
    },
};
