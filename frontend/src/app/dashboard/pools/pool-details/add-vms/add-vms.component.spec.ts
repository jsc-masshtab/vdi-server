import { CUSTOM_ELEMENTS_SCHEMA, NO_ERRORS_SCHEMA } from '@angular/core';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { of } from 'rxjs';

import { AddVMStaticPoolComponent } from './add-vms.component';
import { PoolDetailsService } from '../pool-details.service';

describe('AddVMStaticPoolComponent', () => {
  let component: AddVMStaticPoolComponent;
  let fixture: ComponentFixture<AddVMStaticPoolComponent>;

  let poolServiceStub: Partial<PoolDetailsService>;

  beforeEach(async(() => {
    poolServiceStub = {
      getAllVms(): any {
        return of([]);
      }
    };

    TestBed.configureTestingModule({
      declarations: [ AddVMStaticPoolComponent ],
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
    fixture = TestBed.createComponent(AddVMStaticPoolComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
