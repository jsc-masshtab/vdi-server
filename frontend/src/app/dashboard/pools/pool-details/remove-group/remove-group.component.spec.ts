import { CUSTOM_ELEMENTS_SCHEMA, NO_ERRORS_SCHEMA } from '@angular/core';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';

import { RemoveGroupComponent } from './remove-group.component';
import { PoolDetailsService } from '../pool-details.service';

describe('RemoveGroupComponent', () => {
  let component: RemoveGroupComponent;
  let fixture: ComponentFixture<RemoveGroupComponent>;

  let serviceStub: Partial<PoolDetailsService>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ RemoveGroupComponent ],
      providers: [
        {
          provide: MatDialogRef,
          useValue: {}
        },
        {
          provide: MAT_DIALOG_DATA,
          useValue: {}
        },
        {
          provide: PoolDetailsService,
          useValue: serviceStub
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
    fixture = TestBed.createComponent(RemoveGroupComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
