import { CUSTOM_ELEMENTS_SCHEMA, NO_ERRORS_SCHEMA } from '@angular/core';
import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';

import { RemoveUsersPoolComponent } from './remove-users.component';
import { PoolDetailsService } from '../pool-details.service';
import { of } from 'rxjs';

describe('RemoveUsersPoolComponent', () => {
  let component: RemoveUsersPoolComponent;
  let fixture: ComponentFixture<RemoveUsersPoolComponent>;

  let poolServiceStub: Partial<PoolDetailsService>;

  beforeEach(waitForAsync(() => {
    poolServiceStub = {
      getAllUsersEntitleToPool(): any {
        return of([]);
      }
    };

    TestBed.configureTestingModule({
      declarations: [ RemoveUsersPoolComponent ],
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
    fixture = TestBed.createComponent(RemoveUsersPoolComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
