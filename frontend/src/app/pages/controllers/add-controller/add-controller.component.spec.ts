import { CUSTOM_ELEMENTS_SCHEMA, NO_ERRORS_SCHEMA } from '@angular/core';
import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatDialogRef } from '@angular/material/dialog';

import { ControllersService } from '../all-controllers/controllers.service';
import { AddControllerComponent } from './add-controller.component';

describe('AddControllerComponent', () => {
  let component: AddControllerComponent;
  let fixture: ComponentFixture<AddControllerComponent>;

  let serviceStub: Partial<ControllersService>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      imports: [
        ReactiveFormsModule,
        FormsModule
      ],
      declarations: [ AddControllerComponent ],
      providers: [
        {
          provide: ControllersService,
          useValue: serviceStub
        },
        {
          provide: MatDialogRef,
          useValue: {}
        }
      ],
      schemas: [
        CUSTOM_ELEMENTS_SCHEMA,
        NO_ERRORS_SCHEMA
      ]
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
