const Post = require('../models/Post');

exports.getPosts = async (req, res, next) => {
  try {
    const posts = await Post.find().populate('user', 'username email');
    res.status(200).json({ success: true, count: posts.length, data: posts });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
};

exports.createPost = async (req, res, next) => {
  try {
    req.body.user = req.user.id;
    const post = await Post.create(req.body);
    res.status(201).json({ success: true, data: post });
  } catch (err) {
    res.status(400).json({ success: false, error: err.message });
  }
};

exports.getPost = async (req, res, next) => {
  try {
    const post = await Post.findById(req.params.id).populate('user', 'username email');
    if (!post) {
      return res.status(404).json({ success: false, error: 'Post not found' });
    }
    res.status(200).json({ success: true, data: post });
  } catch (err) {
    res.status(400).json({ success: false, error: err.message });
  }
};

// @desc    Update post
// @route   PUT /api/posts/:id
// @access  Private
exports.updatePost = async (req, res, next) => {
  try {
    let post = await Post.findById(req.params.id);
    if (!post) {
      return res.status(404).json({ success: false, error: 'Post not found' });
    }

    // Make sure user is owner
    if (post.user.toString() !== req.user.id) {
      return res.status(401).json({ success: false, error: 'Not authorized to update this post' });
    }

    post = await Post.findByIdAndUpdate(req.params.id, req.body, {
      new: true,
      runValidators: true
    });

    res.status(200).json({ success: true, data: post });
  } catch (err) {
    res.status(400).json({ success: false, error: err.message });
  }
};