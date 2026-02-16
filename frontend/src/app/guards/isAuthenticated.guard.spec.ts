import { TestBed } from '@angular/core/testing';

import { isAuthenticatedGuard } from './isAuthenticated.guard';

describe('isAuthenticatedGuard', () => {
  let guard: isAuthenticatedGuard;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    guard = TestBed.inject(isAuthenticatedGuard);
  });

  it('should be created', () => {
    expect(guard).toBeTruthy();
  });
});
