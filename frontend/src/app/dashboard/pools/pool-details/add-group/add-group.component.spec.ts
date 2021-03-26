import { CUSTOM_ELEMENTS_SCHEMA, NO_ERRORS_SCHEMA } from '@angular/core';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';

import { AddGropComponent } from './add-group.component';
import { PoolDetailsService } from '../pool-details.service';

describe('AddGropComponent', () => {
  let component: AddGropComponent;
  let fixture: ComponentFixture<AddGropComponent>;

  let serviceStub: Partial<PoolDetailsService>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ AddGropComponent ],
      providers: [
        {
          provide: PoolDetailsService,
          useValue: serviceStub
        },
        {
          provide: MatDialogRef,
          useValue: {}
        },
        {
          provide: MAT_DIALOG_DATA,
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
    fixture = TestBed.createComponent(AddGropComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
