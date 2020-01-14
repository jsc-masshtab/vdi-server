import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { AddAuthenticationDirectoryComponent } from './add-auth-directory.component';

describe('AddUserComponent', () => {
  let component: AddAuthenticationDirectoryComponent;
  let fixture: ComponentFixture<AddAuthenticationDirectoryComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [AddAuthenticationDirectoryComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AddAuthenticationDirectoryComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
