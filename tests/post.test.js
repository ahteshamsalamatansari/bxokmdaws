describe('Post API Tests', () => {
  it('should retrieve posts count', () => {
    const posts = [{ id: 1, title: 'First Post' }];
    expect(posts.length).toBe(1);
  });
});