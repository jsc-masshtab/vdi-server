import { CUSTOM_ELEMENTS_SCHEMA, NO_ERRORS_SCHEMA } from '@angular/core';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';

import { RemoveVMStaticPoolComponent } from './remove-vms.component';
import { PoolDetailsService } from '../pool-details.service';

describe('RemoveVMStaticPoolComponent', () => {
  let component: RemoveVMStaticPoolComponent;
  let fixture: ComponentFixture<RemoveVMStaticPoolComponent>;

  let poolServiceStub: Partial<PoolDetailsService>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ RemoveVMStaticPoolComponent ],
      providers: [
        {
          provide: PoolDetailsService,
          useValue: poolServiceStub
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
    fixture = TestBed.createComponent(RemoveVMStaticPoolComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
