import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { AddControllerComponent } from './add-controller.component';

describe('AddControllerComponent', () => {
  let component: AddControllerComponent;
  let fixture: ComponentFixture<AddControllerComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ AddControllerComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AddControllerComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
