import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ResourseIntoComponent } from './resourse-into.component';

describe('ResourseIntoComponent', () => {
  let component: ResourseIntoComponent;
  let fixture: ComponentFixture<ResourseIntoComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ResourseIntoComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ResourseIntoComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
