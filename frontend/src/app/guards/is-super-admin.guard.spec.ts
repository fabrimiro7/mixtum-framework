import { TestBed } from '@angular/core/testing';

import { IsSuperAdminGuard } from './is-super-admin.guard';

describe('IsSuperAdminGuard', () => {
  let guard: IsSuperAdminGuard;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    guard = TestBed.inject(IsSuperAdminGuard);
  });

  it('should be created', () => {
    expect(guard).toBeTruthy();
  });
});
