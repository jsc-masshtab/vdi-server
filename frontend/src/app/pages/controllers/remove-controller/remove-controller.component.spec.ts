import { CUSTOM_ELEMENTS_SCHEMA, NO_ERRORS_SCHEMA } from '@angular/core';
import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { RouterTestingModule } from '@angular/router/testing';

import { ControllersService } from '../all-controllers/controllers.service';
import { RemoveControllerComponent } from './remove-controller.component';

describe('RemoveControllerComponent', () => {
  let component: RemoveControllerComponent;
  let fixture: ComponentFixture<RemoveControllerComponent>;

  let serviceStub: Partial<ControllersService>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      imports: [ RouterTestingModule ],
      declarations: [ RemoveControllerComponent ],
      providers: [
        {
          provide: ControllersService,
          useValue: serviceStub
        },
        {
          provide: MatDialogRef,
          useValue: {}
        },
        {
          provide: MAT_DIALOG_DATA,
          useValue: {}
        },
      ],
      schemas: [
        CUSTOM_ELEMENTS_SCHEMA,
        NO_ERRORS_SCHEMA
      ]
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
