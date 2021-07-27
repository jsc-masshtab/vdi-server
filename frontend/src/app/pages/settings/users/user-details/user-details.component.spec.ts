import { CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { MatDialog } from '@angular/material/dialog';
import { RouterTestingModule } from '@angular/router/testing';
import { of } from 'rxjs';

import { UsersService } from '../users.service';
import { UserDetailsComponent } from './user-details.component';

describe('UserDetailsComponent', () => {
  let component: UserDetailsComponent;
  let fixture: ComponentFixture<UserDetailsComponent>;

  let dialogStub: Partial<MatDialog>;
  let serviceStub: Partial<UsersService>;

  beforeEach(waitForAsync(() => {
    serviceStub = {
      getUser(): any {
        return {
          valueChanges: of({
            data: {
              user: ''
            }
          })
        };
      }
    };
  
    TestBed.configureTestingModule({
      imports: [RouterTestingModule],
      declarations: [ UserDetailsComponent ],
      providers: [
        {
          provide: MatDialog,
          useValue: dialogStub
        },
        {
          provide: UsersService,
          useValue: serviceStub
        }
      ],
      schemas: [ CUSTOM_ELEMENTS_SCHEMA ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(UserDetailsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
