# wordpress-markdown-blog-loader
This utility loads markdown blogs into Wordpress as a post. It allows you to work on your blog
in your favorite editor and keeps all your blogs in git.

## features
- converts markdown into plain html, with syntax hightlighting support
- uploads and synchronizes any locally referenced images
- generates an opengraph image including the title, subtitle and author in Binx.io or xebia.com style
- sets the Rankmath focus keywords
- sets the canonical url, if specified

## caveats
- changing the slug may orphan images
- removing images from the markdown, will leave dangling images in Wordpress
- you cannot edit via WP and via the uploader, without confusing yourself

## required Wordpress Plugins

- [Rankmath](https://rankmath.com/wordpress/plugin/seo-suite)
- [REST API Meta Support](https://wordpress.org/plugins/rest-api-meta-support/)

Furthermore, you have to enable the Rest API for the [Custom Field Group](https://www.advancedcustomfields.com/resources/wp-rest-api-integration/#enabling-the-rest-api-for-your-acf-fields) for the field `show_header_image`.

## Installation
Install it with [pipx](https://pypa.github.io/pipx/) or use Docker (see below):
```shell
pipx install wordpress-markdown-blog-loader
```

## configuration
to configure the access credentials, you need to add your WordPress application password to the file `~/.wordpress.ini`  
and add a section for your Wordpress installation:

```
[DEFAULT]
host = xebia.com

[xebia.com]
api_host = xebiainnovationproject.kinsta.cloud
username = <your wordpress username>
```

## api host
If the site is served through a CDN, you can also set the `api_host` which will be used as the hostname to invoke the WP REST API. 

## password
To authenticate you need an [application password](https://wordpress.com/support/security/two-step-authentication/application-specific-passwords/), which is different from the user password.

We recommend to store  your application password in 1password and set the environment variable
  WP_APP_PASSWORD using the [1password CLI](https://developer.1password.com/docs/cli):

```shell
WP_APP_PASSWORD="$(op read "op://Private/wordpress app password/password")" wp-md ...
```

## Never touch the WP editor again

Once you start to manage your blogs via this uploader, *do not edit* the blog via one of the WP editors. The editors are weird,
because it appears to make a copy of the content on which you get a WYSIWIG viewer. Unfortunately, it does not detect changes
in the actual blog content. It will look like your uploaded changes are not applied (but they are).

## Using the docker image
To use the docker image as a command line utility, create the following alias:

```bash
alias wp-md='docker run \
 -e WP_APP_PASSWORD="$(op read "op://Private/wordpress app password/password")" \
 -v $HOME:$HOME \
 -v $HOME/.wordpress.ini:/root/.wordpress.ini \
 -v $PWD:/$PWD \
 -w $PWD ghcr.io/binxio/wordpress-markdown-blog-loader:1.6.3
```'
Assuming that your WordPress app password is stored in the 1password Private vault under the name `wordpress app password`

## start a new blog
To start a new blog, type:

```bash
$ wp-md posts new \
	--title "How to create a WordPress blog without touching WordPress" \
        --subtitle "using the wp-md utility" \
	--author "Mark van Holsteijn" \
	--image ~/Downloads/background-image.jpg \
        --image-credits "image by xyz"
INFO: resizing 1920x1920 to 1200x1200
INFO: cropping to maximum height of 630px
INFO: start editing index.md in ./how-to-create-a-wordpress-blog-without-touching-wordpress
```

A skaffold frontmatter blog is created, and you can start writing in the index.md.

##  frontmatter properties
You can set the following properties in the frontmatter:

| Name           | description                                                                                                                                                                                                                                                                  |
|----------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| title          | of the blog                                                                                                                                                                                                                                                                  |
| subtitle       | of the blog, used in the og.image                                                                                                                                                                                                                                            |
| focus-keywords | the SEO focus keywords                                                                                                                                                                                                                                                       
| excerpt        | excerpt of the blog                                                                                                                                                                                                                                                          |
| author         | display name of the author in Wordpress                                                                                                                                                                                                                                      |
| email          | email address of the author, used to lookup profile picture on gravatar.com                                                                                                                                                                                                  |
| author-id      | Wordpress author slug: used to select the appropriate user if multiple users with the same name exists in WP and we cannot read the email address                                                                                                                            |
| categories     | list of wordpress categories for this blog                                                                                                                                                                                                                                   |
| slug           | slug of the blog                                                                                                                                                                                                                                                             |
| date           | on which the blog should be published ISO timestamp format                                                                                                                                                                                                                   |
| status         | draft or publish. if publish, the blog will be published on the `date`                                                                                                                                                                                                       |
| canonical      | url of the blog, to be used in cross posts                                                                                                                                                                                                                                   |
| image          | the banner image of the blog                                                                                                                                                                                                                                                 |
| og.image       | the open graph image of the blog, used in links from social media                                                                                                                                                                                                            |
| og.description | the open graph description of the blog, used in links from social media                                                                                                                                                                                                      |
| guid           | the physical URL of the blog. Written by wp-md on upload and download                                                                                                                                                                                                        |
| brand          | xebia.com or xebia.com. defaults to xebia.com                                                                                                                                                                                                                                |
| industries     | zero or more of banking-and-financial-services, energy-utilities, healthcare-life-sciences, insurance, isv-tech, non-profit, private-equity, public-sector, retail-and-consumer-goods, telecom-media                                                                         |
| partners       | zero or more of modernization-experience-based-acceleration-modax, genai-on-google-cloud, monday, cloud-workplace-solutions, cloud-workplace, google-workplace-tools, workplace-security, workplace-optimization, microsoft-library, developer-productivity-with-github-copilot |
| capabilities   | zero or more of agile-transformation, applied-and-genai, cloud, data-analytics, devops-sre, digital-product-management, intelligent-automation, it-strategy, platform-engineering, product-platform-development                                                              | 

## adding images
To add an image to your blog, add the images in the ./images subdirectory and add a relative reference in markdown. For instance:

```markdown
![](./images/architecture.png)
```

## uploading a blog
To upload a blog, type:

```
$ wp-md posts upload --host xebia.com .
INFO: generating og:image based on images/banner.jpg
INFO: generating new image in how-to-create-a-wordpress-blog-without-touching-wordpress/images/og-banner.jpg
INFO: add logo
INFO: add title
INFO: add subtitle
INFO: add author
INFO: og image saved to how-to-create-a-wordpress-blog-without-touching-wordpress/images/og-banner.jpg
INFO: uploaded blog 'How to create a WordPress blog without touching WordPress' as post https://xebia.com/?p=9625
INFO: updating opengraph image to https://xebia.com/wp-content/uploads/2023/01/how-to-create-a-wordpress-blog-without-touching-wordpress-og-banner.jpg
INFO: post available at https://xebia.com/?p=9625
INFO: uploading image as how-to-create-a-wordpress-blog-without-touching-wordpress-og-banner.jpg
INFO: uploading image as how-to-create-a-wordpress-blog-without-touching-wordpress-banner.jpg
```

## updating / publishing a blog
You can update the blog, by uploading it again.  If you change the status to 'publish' in the frontmatter metadata,
the blog will be published on the specified date.

```
$ wp-md posts upload --host xebia.com .
```

## updating banner and open graph images
You can update the banner and open graph images as follows:

```
$ wp-md posts update-banner . new-banner.jpg
```

## downloading an existing blog
to download an existing blog and convert it to markdown, type:

```
$ wp-md posts download --host xebia.com --directory /tmp 9625
INFO: downloading https://xebia.com/wp-content/uploads/2023/01/how-to-create-a-wordpress-blog-without-touching-wordpress-banner.jpg as banner.jpg
INFO: downloading https://xebia.com/wp-content/uploads/2023/01/how-to-create-a-wordpress-blog-without-touching-wordpress-og-banner.jpg as og-banner.jpg
INFO: writing /tmp/2023/01/how-to-create-a-wordpress-blog-without-touching-wordpress/index.md
```

