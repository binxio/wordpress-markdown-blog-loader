# wordpress-markdown-blog-loader
This utility loads markdown blogs into Wordpress as a post. It allows you to work on your blog
in your favorite editor and keeps all your blogs in git.

## features
- converts markdown into plain html, with syntax hightlighting support
- uploads and synchronizes any locally referenced images
- generates an opengraph image including the title, subtitle and author in Binx.io or xebia.com style

## caveats
- changing the slug may orphan images
- removing images from the markdown, will leave dangling images in Wordpress

## required Wordpress Plugins
- [Yoast SEO](https://wordpress.org/plugins/wordpress-seo/)
- [REST API Meta Support](https://wordpress.org/plugins/rest-api-meta-support/)

## configuration
to configure the access credentials, you need to add your WordPress application password to the file `~/.wordpress.ini`  
and add a section for your Wordpress installation:

```
[DEFAULT]
host = example.com

[example.com]
api_host = example.wpengine.com
username = <your wordpress username>
password = <your application passwoird>
```
Note that the application password is different from the password you use to login to your WordPress installation.

## Using the image
To use the docker image, you have to login using a GitHub container registry access token:

1. Browse to https://github.com/settings/tokens
2. Create new token with 'read:packages' permission
3. Copy the token
4. login to  ghcr.io with Docker.

   `pbpaste | docker login ghcr.io -u <github username> --password-stdin`


## set an alias
To use the docker image as a command line utility, create the following alias:

```bash
alias wp-md='docker run -v $HOME:$HOME -v $HOME/.wordpress.ini:/root/.wordpress.ini -v $PWD:/$PWD -w $PWD ghcr.io/binxio/wordpress-markdown-blog-loader:main'
```

## start a new blog
To start a new blog, type:

```bash
$ wp-md posts new \
	--title "How to create a WordPress blog without touching WordPress" \
        --subtitle "using the wp-md utility" \
	--author "Mark van Holsteijn" \
	--image ~/Downloads/background-image.jpg
INFO: resizing 1920x1920 to 1200x1200
INFO: cropping to maximum height of 630px
INFO: start editing index.md in ./how-to-create-a-wordpress-blog-without-touching-wordpress
```

A skaffold frontmatter blog is created, and you can start writing in the index.md.

## adding images
To add an image to your blog, add the images in the ./images subdirectory and add a relative reference in markdown. For instance:

```markdown
![](./images/architecture.png)
```

## uploading a blog
To upload a blog, type:

```
$ wp-md posts upload --host binx.io .
INFO: generating og:image based on images/banner.jpg
INFO: generating new image in how-to-create-a-wordpress-blog-without-touching-wordpress/images/og-banner.jpg
INFO: add logo
INFO: add title
INFO: add subtitle
INFO: add author
INFO: og image saved to how-to-create-a-wordpress-blog-without-touching-wordpress/images/og-banner.jpg
INFO: uploaded blog 'How to create a WordPress blog without touching WordPress' as post https://binx.io/?p=9625
INFO: updating opengraph image to https://binx.io/wp-content/uploads/2023/01/how-to-create-a-wordpress-blog-without-touching-wordpress-og-banner.jpg
INFO: post available at https://binx.io/?p=9625
INFO: uploading image as how-to-create-a-wordpress-blog-without-touching-wordpress-og-banner.jpg
INFO: uploading image as how-to-create-a-wordpress-blog-without-touching-wordpress-banner.jpg
```

## updating / publishing a blog
You can update the blog, by uploading it again.  If you change the status to 'publish' in the frontmatter metadata,
the blog will be published on the specified date.

```
$ wp-md posts upload --host binx.io .
```

## downloading an existing blog
to download an existing blog and convert it to markdown, type:

```
$ wp-md posts download --host binx.io --directory /tmp 9625
INFO: downloading https://binx.io/wp-content/uploads/2023/01/how-to-create-a-wordpress-blog-without-touching-wordpress-banner.jpg as banner.jpg
INFO: downloading https://binx.io/wp-content/uploads/2023/01/how-to-create-a-wordpress-blog-without-touching-wordpress-og-banner.jpg as og-banner.jpg
INFO: writing /tmp/2023/01/how-to-create-a-wordpress-blog-without-touching-wordpress/index.md
```

