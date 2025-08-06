---
title: "hexo hugo vuepress 文档写法区别"
categories:
  - Hexo
tags:
  - Hexo
  - Hugo
  - VuePress
date: 2025-07-06 13:18:30
---
> 摘要: hexo hugo vuepress 文档写法区别

<!-- more -->

------

# 区别

## hexo写法

```yaml
---
title: 标题1
date: 2025-07-06 13:18:30
# 分类 区分上下级
categories:
  - 父分类1
  - 子分类1-1
tags:
  - 标签1
  - 标签2
# 禁止评论 ,不兼容 迁移博客时需要手动处理
comments: false
# 文章更新日期 ,不兼容 迁移博客时需要手动处理
updated: 2025-07-06 13:18:30
---
```

## hugo next 写法

```yaml
---
# 标题最好带双引号 要不带空格的话 会报错
title: "标题1"
date: 2025-07-06 13:18:30
# 分类 区分上下级
categories:
  - 父分类1
  - 子分类1-1
tags:
  - 标签1
  - 标签2
# 禁止评论,不兼容 迁移博客时需要手动处理
comment:
  enable: false
# 文章更新日期 ,不兼容 迁移博客时需要手动处理
lastmod: 2025-07-06 13:18:30
---
```

## Vuepress2 hope 写法

```yaml
---
title: "标题1"
date: 2025-07-06 13:18:30
# 分类 不区分上下级 兼容categories  无损迁移
category:
  - 分类1
  - 分类2
# 标签 兼容tags 无损迁移
tag:
  - 标签1
  - 标签2
# 禁止评论,不兼容 迁移博客时需要手动处理
comment: false
---

```

# 总结

建议使用以下模版 兼容3个

```
---
title: "标题1"
date: 2025-07-06 13:18:30
# 分类 区分上下级
categories:
  - 父分类1
  - 子分类1-1
tags:
  - 标签1
  - 标签2
---
```

# 扩展

## Astro主题AstroWind写法

https://github.com/onwidget/astrowind

```
---
title: Hexo多分类多标签图片路径写作教程
publishDate: 2025-05-30 11:19:04
category: Hexo
tags: 
 - Hexo
---
```

## Astro主题fuwari写法

https://github.com/saicaca/fuwari

```
---
title: Simple Guides for Fuwari
published: 2024-04-01
tags: ["Fuwari", "Blogging", "Customization"]
category: Guides  #分类好像不支持数组 必须为字符串 通过二次开发改为数组 支持多分类
---
如果tags给空 必须这么写
tags: []
```

## mkdocs-material写法

https://github.com/squidfunk/mkdocs-material

```
---
title: 中文标题测试文章
date: 2025-05-30 19:13:23
categories: 
 - 中文分类
tags: 
 - 中文标签
---
```

## Docusaurus写法

```
---
title: 中文标题测试文章1
date: 2025-05-31 19:13:23
tags: 
 - 中文标签
---
<!-- more --> 不好使 改为 <!-- truncate -->  通过配置可以修改为<!-- more -->

categories: 中文分类           好像不支持分类 打算用作者添加分类
```

