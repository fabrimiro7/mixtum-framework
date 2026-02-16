import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TutorialAddComponent } from './tutorial-add.component';

describe('TutorialAddComponent', () => {
  let component: TutorialAddComponent;
  let fixture: ComponentFixture<TutorialAddComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ TutorialAddComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(TutorialAddComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
