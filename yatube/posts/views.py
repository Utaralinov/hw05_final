from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User
from .utils import get_paginator


def index(request):
    template = 'posts/index.html'
    title = "Последние обновления на сайте"
    post_list = Post.objects.all()
    page_number = request.GET.get('page')
    context = {
        'page_obj': get_paginator(post_list, page_number),
        'title': title,
        'index': True
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    post_list = Post.objects.filter(group=group)
    page_number = request.GET.get('page')

    context = {
        'group': group,
        'page_obj': get_paginator(post_list, page_number),
    }
    return render(request, template, context)


def profile(request, username):
    profile = get_object_or_404(User, username=username)
    post_list = Post.objects.filter(author=profile)
    posts_count = post_list.count()
    page_number = request.GET.get('page')
    following = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(user=request.user,
                                          author=profile).exists
    context = {
        'profile': profile,
        'page_obj': get_paginator(post_list, page_number),
        'posts_count': posts_count,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    posts_count = Post.objects.filter(author=post.author).count()
    comments = Comment.objects.filter(post=post)
    context = {
        'post': post,
        'posts_count': posts_count,
        'form': CommentForm(),
        'comments': comments
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()

        return redirect('posts:profile', username=post.author)

    template = 'posts/create_post.html'
    context = {
        'form': form
    }
    return render(request, template, context)


@login_required
def post_edit(request, pid):
    post = get_object_or_404(Post, pk=pid)
    user = request.user
    if user != post.author:
        return redirect('posts:post_detail', post_id=pid)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )

    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=pid)

    context = {
        'form': form,
        'is_edit': True
    }

    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    title = "Последние обновления подписок"
    following = request.user.follower.all()
    authors = map(lambda follow: follow.author, following)
    post_list = Post.objects.filter(author__in=authors)
    page_number = request.GET.get('page')
    context = {
        'page_obj': get_paginator(post_list, page_number),
        'title': title,
        'follow': True
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    try:
        Follow.objects.create(
            user=request.user,
            author=author
        )
    except ValidationError:
        pass
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(
        user=request.user,
        author=author
    ).delete()
    return redirect('posts:profile', username=username)
