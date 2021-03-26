import { CUSTOM_ELEMENTS_SCHEMA, NO_ERRORS_SCHEMA } from '@angular/core';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { MatDialog, MAT_DIALOG_DATA } from '@angular/material/dialog';

import { VmDetalsPopupComponent } from './vm-details-popup.component';
import { PoolDetailsService } from '../pool-details.service';

describe('VmDetalsPopupComponent', () => {
  let component: VmDetalsPopupComponent;
  let fixture: ComponentFixture<VmDetalsPopupComponent>;

  let poolServiceStub: Partial<PoolDetailsService>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ VmDetalsPopupComponent ],
      providers: [
        {
          provide: PoolDetailsService,
          useValue: poolServiceStub
        },
        {
          provide: MatDialog,
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
    fixture = TestBed.createComponent(VmDetalsPopupComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
