import { CUSTOM_ELEMENTS_SCHEMA, NO_ERRORS_SCHEMA } from '@angular/core';
import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';

import { PoolDetailsService } from '../pool-details.service';
import { PrepareVmPoolComponent } from './prepare-vm.component';

describe('PrepareVmPoolComponent', () => {
  let component: PrepareVmPoolComponent;
  let fixture: ComponentFixture<PrepareVmPoolComponent>;

  let poolServiceStub: Partial<PoolDetailsService>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ PrepareVmPoolComponent ],
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
    fixture = TestBed.createComponent(PrepareVmPoolComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
