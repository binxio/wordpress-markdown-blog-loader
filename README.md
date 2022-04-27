# wordpress-markdown-blog-loader
This utility loads markdown blogs into Wordpress as a post. It allows you to work on your blog
in your favorite editor and keeps all your blogs in git.

## features
- converts markdown into plain html, with syntax hightlighting support
- uploads and synchronizes any locally referenced images
- generates an opengraph image including the title, subtitle and author in Binx.io style

## caveats
- changing the slug leaves may orphan blog and images
- removing images from the markdown, will leave dangling images in Wordpress

## required Wordpress Plugins
- [Yoast SEO](https://wordpress.org/plugins/wordpress-seo/)
- [REST API Meta Support](https://wordpress.org/plugins/rest-api-meta-support/)

## configuration
to configure the access credentials, add the file `~/.wordpress.ini` and add a section
for your Wordpress installation:

```
[DEFAULT]
host = example.com

[example.com]
api_host = example.wpengine.com
username = <your wordpress username>
password = <your application passwoird>
```
