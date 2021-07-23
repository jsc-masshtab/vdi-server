import { CUSTOM_ELEMENTS_SCHEMA, NO_ERRORS_SCHEMA } from '@angular/core';
import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { of } from 'rxjs';

import { AddUsersPoolComponent } from './add-users.component';
import { PoolDetailsService } from '../pool-details.service';

describe('AddUsersPoolComponent', () => {
  let component: AddUsersPoolComponent;
  let fixture: ComponentFixture<AddUsersPoolComponent>;

  let poolServiceStub: Partial<PoolDetailsService>;

  beforeEach(waitForAsync(() => {
    poolServiceStub = {
      getAllUsersNoEntitleToPool(): any {
        return of([]);
      }
    };

    TestBed.configureTestingModule({
      declarations: [ AddUsersPoolComponent ],
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
      schemas: [ CUSTOM_ELEMENTS_SCHEMA, NO_ERRORS_SCHEMA ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AddUsersPoolComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
