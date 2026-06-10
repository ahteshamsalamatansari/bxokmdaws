const regHandler = (username, email) => {
  if(!username || !email) return { error: 'Details missing' };
  return { id: 1, username };
};

describe('Auth Registration Integration', () => {
  it('should register a user when details are correct', () => {
    const res = regHandler('john_doe', 'john@gmail.com');
    expect(res.username).toBe('john_doe');
    expect(res.id).toBe(1);
  });
  
  it('should return error when username is missing', () => {
    const res = regHandler('', 'john@gmail.com');
    expect(res.error).toBe('Details missing');
  });
});