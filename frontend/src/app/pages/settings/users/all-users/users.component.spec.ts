import { CUSTOM_ELEMENTS_SCHEMA, NO_ERRORS_SCHEMA } from '@angular/core';
import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { MatDialog } from '@angular/material/dialog';
import { RouterTestingModule } from '@angular/router/testing';
import { of } from 'rxjs';

import { UsersService } from '../users.service';
import { UsersComponent } from './users.component';

describe('UsersComponent', () => {
  let component: UsersComponent;
  let fixture: ComponentFixture<UsersComponent>;

  let serviceStub: Partial<UsersService>;

  beforeEach(waitForAsync(() => {
    serviceStub = {
      getAllUsers(): any {
        return {
          valueChanges: of({
            data: {
              users: [],
              count: []
            }
          })
        };
      },
      paramsForGetUsers: {
        spin: false
      }
    };

    TestBed.configureTestingModule({
      imports: [RouterTestingModule],
      declarations: [UsersComponent ],
      providers: [
        {
          provide: MatDialog,
          useValue: {}
        },
        {
          provide: UsersService,
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
    fixture = TestBed.createComponent(UsersComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
