import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { RemoveControllerComponent } from './remove-controller.component';

describe('AddControllerComponent', () => {
  let component: AddControllerComponent;
  let fixture: ComponentFixture<AddControllerComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ RemoveControllerComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(RemoveControllerComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
